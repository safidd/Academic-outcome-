/**
 * Offline-First Attendance System
 * Implements client-side storage and background synchronization
 */

class AttendanceOfflineStorage {
    constructor() {
        this.dbName = 'academic_tracker_attendance';
        this.dbVersion = 1;
        this.storeName = 'pending_attendance';
        this.db = null;
        this.syncInProgress = false;
    }

    /**
     * Initialize IndexedDB database
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object store if it doesn't exist
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const objectStore = db.createObjectStore(this.storeName, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    
                    // Create indexes for efficient querying
                    objectStore.createIndex('course_id', 'course_id', { unique: false });
                    objectStore.createIndex('date', 'date', { unique: false });
                    objectStore.createIndex('sync_status', 'sync_status', { unique: false });
                    objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                }
            };
        });
    }

    /**
     * Generate unique ID for attendance record
     */
    generateId(courseId, date, studentId) {
        return `${courseId}_${date}_${studentId}`;
    }

    /**
     * Save attendance record to IndexedDB (offline-first)
     */
    async saveAttendance(courseId, date, attendanceData) {
        if (!this.db) {
            await this.init();
        }

        const records = [];
        const timestamp = new Date().toISOString();

        for (const [studentId, status] of Object.entries(attendanceData)) {
            const recordId = this.generateId(courseId, date, studentId);
            
            const record = {
                id: recordId,
                course_id: courseId,
                date: date,
                student_id: parseInt(studentId),
                status: status,
                sync_status: 'pending',
                timestamp: timestamp,
                retry_count: 0
            };

            records.push(record);
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);

            const requests = records.map(record => {
                // Use put to handle duplicates (idempotent)
                return store.put(record);
            });

            Promise.all(requests.map(req => {
                return new Promise((res, rej) => {
                    req.onsuccess = () => res();
                    req.onerror = () => rej(req.error);
                });
            }))
            .then(() => {
                resolve(records.length);
            })
            .catch(reject);
        });
    }

    /**
     * Get all pending attendance records
     */
    async getPendingRecords() {
        if (!this.db) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const index = store.index('sync_status');
            const request = index.getAll('pending');

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    /**
     * Mark records as synced
     */
    async markAsSynced(recordIds) {
        if (!this.db) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);

            const requests = recordIds.map(id => {
                const getRequest = store.get(id);
                return new Promise((res, rej) => {
                    getRequest.onsuccess = () => {
                        const record = getRequest.result;
                        if (record) {
                            record.sync_status = 'synced';
                            const putRequest = store.put(record);
                            putRequest.onsuccess = () => res();
                            putRequest.onerror = () => rej(putRequest.error);
                        } else {
                            res();
                        }
                    };
                    getRequest.onerror = () => rej(getRequest.error);
                });
            });

            Promise.all(requests)
                .then(() => resolve())
                .catch(reject);
        });
    }

    /**
     * Delete synced records older than 7 days
     */
    async cleanupOldRecords() {
        if (!this.db) {
            await this.init();
        }

        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const index = store.index('sync_status');
            const request = index.openCursor();

            const deletePromises = [];

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    const record = cursor.value;
                    if (record.sync_status === 'synced' && 
                        new Date(record.timestamp) < sevenDaysAgo) {
                        deletePromises.push(
                            new Promise((res, rej) => {
                                const deleteRequest = cursor.delete();
                                deleteRequest.onsuccess = () => res();
                                deleteRequest.onerror = () => rej(deleteRequest.error);
                            })
                        );
                    }
                    cursor.continue();
                } else {
                    Promise.all(deletePromises)
                        .then(() => resolve())
                        .catch(reject);
                }
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get sync status count
     */
    async getSyncStatus() {
        if (!this.db) {
            await this.init();
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const index = store.index('sync_status');
            
            const pendingRequest = index.count('pending');
            const syncedRequest = index.count('synced');

            let pendingCount = 0;
            let syncedCount = 0;
            let completed = 0;

            const checkComplete = () => {
                completed++;
                if (completed === 2) {
                    resolve({
                        pending: pendingCount,
                        synced: syncedCount,
                        isOnline: navigator.onLine
                    });
                }
            };

            pendingRequest.onsuccess = () => {
                pendingCount = pendingRequest.result;
                checkComplete();
            };

            syncedRequest.onsuccess = () => {
                syncedCount = syncedRequest.result;
                checkComplete();
            };

            pendingRequest.onerror = () => reject(pendingRequest.error);
            syncedRequest.onerror = () => reject(syncedRequest.error);
        });
    }
}

/**
 * Background Synchronization Service
 */
class AttendanceSyncService {
    constructor(storage) {
        this.storage = storage;
        this.syncInProgress = false;
        this.syncUrl = '/instructor/api/sync-attendance/';
    }

    /**
     * Sync pending records to server
     */
    async syncPendingRecords() {
        if (this.syncInProgress || !navigator.onLine) {
            return { success: false, message: 'Sync already in progress or offline' };
        }

        this.syncInProgress = true;

        try {
            const pendingRecords = await this.storage.getPendingRecords();
            
            if (pendingRecords.length === 0) {
                this.syncInProgress = false;
                return { success: true, message: 'No pending records', synced: 0 };
            }

            // Group records by course and date for batch processing
            const groupedRecords = {};
            for (const record of pendingRecords) {
                const key = `${record.course_id}_${record.date}`;
                if (!groupedRecords[key]) {
                    groupedRecords[key] = {
                        course_id: record.course_id,
                        date: record.date,
                        attendance_data: {}
                    };
                }
                groupedRecords[key].attendance_data[record.student_id] = record.status;
            }

            // Sync each group
            let totalSynced = 0;
            const syncedIds = [];

            for (const group of Object.values(groupedRecords)) {
                try {
                    const response = await fetch(this.syncUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCsrfToken()
                        },
                        body: JSON.stringify({
                            course: group.course_id,
                            date: group.date,
                            attendance_data: group.attendance_data
                        })
                    });

                    if (response.ok) {
                        const result = await response.json();
                        if (result.success) {
                            // Mark all records in this group as synced
                            for (const record of pendingRecords) {
                                if (record.course_id === group.course_id && 
                                    record.date === group.date) {
                                    syncedIds.push(record.id);
                                    totalSynced++;
                                }
                            }
                        } else {
                            throw new Error(result.error || 'Sync failed');
                        }
                    } else {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                } catch (error) {
                    console.error('Sync error for group:', error);
                    // Continue with other groups
                }
            }

            // Mark synced records
            if (syncedIds.length > 0) {
                await this.storage.markAsSynced(syncedIds);
            }

            this.syncInProgress = false;
            return {
                success: true,
                message: `Synced ${totalSynced} records`,
                synced: totalSynced
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

    /**
     * Get CSRF token from cookies
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Start automatic sync monitoring
     */
    startAutoSync() {
        // Sync immediately if online
        if (navigator.onLine) {
            this.syncPendingRecords().then(result => {
                this.updateSyncStatus();
            });
        }

        // Listen for online event
        window.addEventListener('online', () => {
            console.log('Connection restored, syncing pending records...');
            this.syncPendingRecords().then(result => {
                this.updateSyncStatus();
                if (result.success && result.synced > 0) {
                    this.showNotification(`Synced ${result.synced} attendance records`);
                }
            });
        });

        // Periodic sync check (every 30 seconds)
        setInterval(() => {
            if (navigator.onLine && !this.syncInProgress) {
                this.syncPendingRecords().then(() => {
                    this.updateSyncStatus();
                });
            }
        }, 30000);
    }

    /**
     * Update sync status indicator
     */
    async updateSyncStatus() {
        const status = await this.storage.getSyncStatus();
        const indicator = document.getElementById('syncStatusIndicator');
        
        if (indicator) {
            if (status.pending > 0) {
                indicator.className = 'sync-status pending';
                indicator.title = `${status.pending} records pending sync`;
                indicator.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 1 1 10-10M22 12.5a10 10 0 1 1-10 10"/>
                </svg> ${status.pending}`;
            } else {
                indicator.className = 'sync-status synced';
                indicator.title = 'All records synced';
                indicator.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>`;
            }

            if (!status.isOnline) {
                indicator.className = 'sync-status offline';
                indicator.title = 'Offline - records will sync when connection is restored';
            }
        }
    }

    /**
     * Show notification
     */
    showNotification(message) {
        // Create or update notification element
        let notification = document.getElementById('syncNotification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'syncNotification';
            notification.className = 'sync-notification';
            document.body.appendChild(notification);
        }

        notification.textContent = message;
        notification.style.display = 'block';

        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }
}

// Initialize global instances
let attendanceStorage = null;
let attendanceSync = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    if (typeof indexedDB !== 'undefined') {
        attendanceStorage = new AttendanceOfflineStorage();
        await attendanceStorage.init();
        
        attendanceSync = new AttendanceSyncService(attendanceStorage);
        attendanceSync.startAutoSync();
        
        // Update status indicator
        attendanceSync.updateSyncStatus();
        
        // Cleanup old records periodically
        setInterval(() => {
            attendanceStorage.cleanupOldRecords();
        }, 3600000); // Every hour
    }
});

