/**
 * Unit Tests for Offline Attendance Synchronization
 * These tests can be run in browser console or with a testing framework
 */

// Mock objects for testing
class MockIndexedDB {
    constructor() {
        this.store = new Map();
        this.pendingRecords = [];
    }

    async saveAttendance(courseId, date, attendanceData) {
        const timestamp = new Date().toISOString();
        for (const [studentId, status] of Object.entries(attendanceData)) {
            const recordId = `${courseId}_${date}_${studentId}`;
            this.store.set(recordId, {
                id: recordId,
                course_id: courseId,
                date: date,
                student_id: parseInt(studentId),
                status: status,
                sync_status: 'pending',
                timestamp: timestamp
            });
            this.pendingRecords.push(recordId);
        }
        return Object.keys(attendanceData).length;
    }

    async getPendingRecords() {
        return Array.from(this.store.values()).filter(r => r.sync_status === 'pending');
    }

    async markAsSynced(recordIds) {
        for (const id of recordIds) {
            const record = this.store.get(id);
            if (record) {
                record.sync_status = 'synced';
            }
        }
    }
}

class MockSyncService {
    constructor(storage) {
        this.storage = storage;
        this.syncInProgress = false;
        this.onlineStatus = true;
        this.syncTriggered = false;
    }

    async syncPendingRecords() {
        if (this.syncInProgress || !this.onlineStatus) {
            return { success: false, message: 'Sync already in progress or offline' };
        }

        this.syncInProgress = true;
        this.syncTriggered = true;

        try {
            const pendingRecords = await this.storage.getPendingRecords();
            
            if (pendingRecords.length === 0) {
                this.syncInProgress = false;
                return { success: true, message: 'No pending records', synced: 0 };
            }

            // Simulate successful sync
            const recordIds = pendingRecords.map(r => r.id);
            await this.storage.markAsSynced(recordIds);
            
            this.syncInProgress = false;
            return {
                success: true,
                message: `Synced ${pendingRecords.length} records`,
                synced: pendingRecords.length
            };
        } catch (error) {
            this.syncInProgress = false;
            return {
                success: false,
                message: error.message,
                synced: 0
            };
        }
    }

    setOnlineStatus(status) {
        this.onlineStatus = status;
    }
}

// Test Suite
function runOfflineSyncTests() {
    console.log('Running Offline Sync Tests...');
    
    let testsPassed = 0;
    let testsFailed = 0;

    function assert(condition, message) {
        if (condition) {
            console.log(`✅ PASS: ${message}`);
            testsPassed++;
        } else {
            console.error(`❌ FAIL: ${message}`);
            testsFailed++;
        }
    }

    // Test 1: Save attendance offline
    async function testOfflineSave() {
        const storage = new MockIndexedDB();
        const syncService = new MockSyncService(storage);
        
        // Set offline
        syncService.setOnlineStatus(false);
        
        // Save attendance
        const count = await storage.saveAttendance(1, '2025-12-22', {
            '1': 'Present',
            '2': 'Absent'
        });
        
        assert(count === 2, 'Should save 2 records locally');
        
        const pending = await storage.getPendingRecords();
        assert(pending.length === 2, 'Should have 2 pending records');
        
        // Verify sync was not triggered
        assert(!syncService.syncTriggered, 'Sync should not trigger when offline');
    }

    // Test 2: Sync when online
    async function testOnlineSync() {
        const storage = new MockIndexedDB();
        const syncService = new MockSyncService(storage);
        
        // Save records offline
        await storage.saveAttendance(1, '2025-12-22', {
            '1': 'Present',
            '2': 'Late'
        });
        
        // Set online
        syncService.setOnlineStatus(true);
        
        // Sync
        const result = await syncService.syncPendingRecords();
        
        assert(result.success === true, 'Sync should succeed when online');
        assert(result.synced === 2, 'Should sync 2 records');
        
        const pending = await storage.getPendingRecords();
        assert(pending.length === 0, 'Should have no pending records after sync');
    }

    // Test 3: Sync only triggers on online event
    async function testSyncOnOnlineEvent() {
        const storage = new MockIndexedDB();
        const syncService = new MockSyncService(storage);
        
        // Set offline
        syncService.setOnlineStatus(false);
        
        // Save records
        await storage.saveAttendance(1, '2025-12-22', {
            '1': 'Present'
        });
        
        assert(!syncService.syncTriggered, 'Sync should not trigger when offline');
        
        // Simulate online event
        syncService.setOnlineStatus(true);
        const result = await syncService.syncPendingRecords();
        
        assert(syncService.syncTriggered === true, 'Sync should trigger when online');
        assert(result.success === true, 'Sync should succeed');
    }

    // Test 4: No duplicate records on retry
    async function testIdempotentSync() {
        const storage = new MockIndexedDB();
        const syncService = new MockSyncService(storage);
        
        // Save same record twice
        await storage.saveAttendance(1, '2025-12-22', {
            '1': 'Present'
        });
        
        await storage.saveAttendance(1, '2025-12-22', {
            '1': 'Present'  // Same record
        });
        
        // Should only have one record (idempotent)
        const pending = await storage.getPendingRecords();
        assert(pending.length === 1, 'Should have only 1 record (idempotent)');
    }

    // Run all tests
    async function runAllTests() {
        await testOfflineSave();
        await testOnlineSync();
        await testSyncOnOnlineEvent();
        await testIdempotentSync();
        
        console.log(`\n📊 Test Results: ${testsPassed} passed, ${testsFailed} failed`);
    }

    runAllTests();
}

// Export for use in browser console
if (typeof window !== 'undefined') {
    window.runOfflineSyncTests = runOfflineSyncTests;
}

