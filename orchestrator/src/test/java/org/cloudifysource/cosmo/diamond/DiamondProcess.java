/*******************************************************************************
 * Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.cloudifysource.cosmo.diamond;

import com.google.common.base.Throwables;
import com.google.common.collect.Queues;
import org.cloudifysource.cosmo.logging.Logger;
import org.cloudifysource.cosmo.logging.LoggerFactory;
import org.cloudifysource.cosmo.tasks.EventListener;
import org.cloudifysource.cosmo.tasks.TaskExecutor;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * TODO: Write a short summary of this type's roles and responsibilities.
 *
 * @author Dan Kilman
 * @since 0.1
 */
public class DiamondProcess implements AutoCloseable {

    private final Logger logger = LoggerFactory.getLogger(this.getClass());
    private final TaskExecutor taskExecutor;
    private final String jsonArgs;

    public DiamondProcess(TaskExecutor taskExecutor,
                          String jsonArgs) throws Exception {
        this.taskExecutor = taskExecutor;
        this.jsonArgs = jsonArgs;
        start();
    }

    private void start() throws Exception {
        executeTask("install");
        executeTask("start");
    }

    @Override
    public void close() throws Exception {
        executeTask("stop");
    }

    private void executeTask(final String operation) throws Exception {
        final BlockingQueue<Object> queue = Queues.newArrayBlockingQueue(1);
        String taskName = "cosmo.cloudify.tosca.artifacts.plugin.diamond_installer.installer.tasks." + operation;
        taskExecutor.sendTask(
                "cloudify.management",
                operation + "_diamond_process",
                taskName,
                jsonArgs,
                new EventListener() {
                    @Override
                    public void onTaskSucceeded(String jsonEvent) {
                        logger.debug("Successfully executed {}: {}", operation, jsonEvent);
                        queue.add(jsonEvent);
                    }

                    @Override
                    public void onTaskFailed(String jsonEvent) {
                        logger.debug("Failed executing {}: {}", operation, jsonEvent);
                        queue.add(new Exception(jsonEvent));
                    }
                });
        Object o = queue.poll(30, TimeUnit.SECONDS);
        if (o instanceof Exception) {
            throw Throwables.propagate((Throwable) o);
        }
    }

}
