package com.talentica.brs.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.lang.reflect.Method;
import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * Async configuration for the Book Review System.
 * Configures thread pools, task executors, and async processing capabilities.
 */
@Slf4j
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {

    /**
     * Core thread pool size for async operations.
     */
    private static final int CORE_POOL_SIZE = 5;

    /**
     * Maximum thread pool size for async operations.
     */
    private static final int MAX_POOL_SIZE = 20;

    /**
     * Queue capacity for async tasks.
     */
    private static final int QUEUE_CAPACITY = 100;

    /**
     * Thread keep-alive time in seconds.
     */
    private static final int KEEP_ALIVE_SECONDS = 60;

    /**
     * Configure the default async task executor.
     * 
     * @return configured ThreadPoolTaskExecutor
     */
    @Bean("taskExecutor")
    public ThreadPoolTaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(CORE_POOL_SIZE);
        executor.setMaxPoolSize(MAX_POOL_SIZE);
        executor.setQueueCapacity(QUEUE_CAPACITY);
        executor.setKeepAliveSeconds(KEEP_ALIVE_SECONDS);
        executor.setThreadNamePrefix("BRS-Async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(30);
        executor.initialize();
        
        log.info("Task executor configured with core={}, max={}, queue={}", 
                CORE_POOL_SIZE, MAX_POOL_SIZE, QUEUE_CAPACITY);
        return executor;
    }

    /**
     * Configure a dedicated executor for recommendation processing.
     * 
     * @return configured ThreadPoolTaskExecutor for recommendations
     */
    @Bean("recommendationExecutor")
    public ThreadPoolTaskExecutor recommendationExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(3);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(50);
        executor.setKeepAliveSeconds(120);
        executor.setThreadNamePrefix("BRS-Recommendation-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(60);
        executor.initialize();
        
        log.info("Recommendation executor configured");
        return executor;
    }

    /**
     * Configure a dedicated executor for email notifications.
     * 
     * @return configured ThreadPoolTaskExecutor for email processing
     */
    @Bean("emailExecutor")
    public ThreadPoolTaskExecutor emailExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(5);
        executor.setQueueCapacity(25);
        executor.setKeepAliveSeconds(300);
        executor.setThreadNamePrefix("BRS-Email-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(120);
        executor.initialize();
        
        log.info("Email executor configured");
        return executor;
    }

    /**
     * Configure a dedicated executor for data processing tasks.
     * 
     * @return configured ThreadPoolTaskExecutor for data processing
     */
    @Bean("dataProcessingExecutor")
    public ThreadPoolTaskExecutor dataProcessingExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(15);
        executor.setQueueCapacity(75);
        executor.setKeepAliveSeconds(180);
        executor.setThreadNamePrefix("BRS-Data-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(90);
        executor.initialize();
        
        log.info("Data processing executor configured");
        return executor;
    }

    /**
     * Get the default async task executor.
     * 
     * @return configured Executor instance
     */
    @Override
    public Executor getAsyncExecutor() {
        return taskExecutor();
    }

    /**
     * Configure exception handler for async methods.
     * 
     * @return configured AsyncUncaughtExceptionHandler
     */
    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return new AsyncUncaughtExceptionHandler() {
            @Override
            public void handleUncaughtException(Throwable ex, Method method, Object... params) {
                log.error("Async method '{}' threw exception: {}", method.getName(), ex.getMessage(), ex);
                
                // Log method parameters for debugging
                if (params != null && params.length > 0) {
                    log.debug("Method parameters: {}", java.util.Arrays.toString(params));
                }
                
                // Additional error handling logic can be added here
                // For example, sending notifications, updating error tracking, etc.
            }
        };
    }

    /**
     * Get thread pool statistics for monitoring.
     * 
     * @param executor the executor to get stats for
     * @return formatted statistics string
     */
    public String getExecutorStats(ThreadPoolTaskExecutor executor) {
        ThreadPoolExecutor threadPool = executor.getThreadPoolExecutor();
        return String.format("Active: %d, Pool Size: %d, Core Pool: %d, Max Pool: %d, Queue: %d", 
                threadPool.getActiveCount(),
                threadPool.getPoolSize(),
                threadPool.getCorePoolSize(),
                threadPool.getMaximumPoolSize(),
                threadPool.getQueue().size());
    }

    /**
     * Log all executor statistics for monitoring purposes.
     */
    public void logExecutorStats() {
        log.info("=== Executor Statistics ===");
        log.info("Task Executor: {}", getExecutorStats(taskExecutor()));
        log.info("Recommendation Executor: {}", getExecutorStats(recommendationExecutor()));
        log.info("Email Executor: {}", getExecutorStats(emailExecutor()));
        log.info("Data Processing Executor: {}", getExecutorStats(dataProcessingExecutor()));
    }
}
