//
// Created by lessju on 26/08/2015.
//

#ifndef _THREADCLASS_H
#define _THREADCLASS_H

#include <pthread.h>
#include <stdio.h>

#define DEBUG

class RealTimeThread
{
    public:
        RealTimeThread() { /* empty */ }
        virtual ~RealTimeThread() { /* empty */}

        // Returns true if the thread was successfully started, false if there was an error starting the thread
        bool startThread()
        {
            pthread_attr_t attr;
            sched_param param;

            // Set thread with maximum priority
            pthread_attr_init(&attr);
            pthread_attr_setschedpolicy(&attr, SCHED_RR);
            param.sched_priority = sched_get_priority_max(SCHED_RR);
            pthread_attr_setschedparam(&attr, &param);

            // Create thread
            return (pthread_create(&_thread, &attr, threadEntryFunc, this) == 0);
        }

        // Set thread affinity
        int setThreadAffinity(unsigned int mask)
        {
            // Create CPU mask
            cpu_set_t cpuset;
            CPU_ZERO(&cpuset);
            CPU_SET(mask, &cpuset);

            // Apply CPU set
            if ((pthread_setaffinity_np(_thread, sizeof(cpu_set_t), &cpuset)) != 0) {
#ifdef DEBUG
                perror("Cannot set pthread affinity");
#else
                // Use syslog
#endif
                return -1;
            }

            return 0;
        }
        // Will not return until the internal thread has exited.
        void waitForThreadToExit()
        {
            (void) pthread_join(_thread, NULL);
        }

    protected:
        // Implement this method in your subclass with the code you want your thread to run.
        virtual void threadEntry() = 0;

    private:
        static void *threadEntryFunc(void *This) { ((RealTimeThread *) This)->threadEntry(); return NULL;}

        pthread_t _thread;
};

#endif // _THREADCLASS_H
