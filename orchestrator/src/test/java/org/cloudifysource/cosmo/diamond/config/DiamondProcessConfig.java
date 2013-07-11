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

package org.cloudifysource.cosmo.diamond.config;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.google.common.base.Throwables;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.io.InputSupplier;
import com.google.common.io.Resources;
import org.cloudifysource.cosmo.diamond.DiamondProcess;
import org.cloudifysource.cosmo.dsl.DSLProcessor;
import org.cloudifysource.cosmo.fileserver.JettyFileServer;
import org.cloudifysource.cosmo.orchestrator.integration.config.TemporaryDirectoryConfig;
import org.cloudifysource.cosmo.tasks.CeleryWorkerProcess;
import org.cloudifysource.cosmo.tasks.TaskExecutor;
import org.hibernate.validator.constraints.NotEmpty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.inject.Inject;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.util.List;
import java.util.Map;

/**
 * Starts a new {@link DiamondProcess} using the celery tasks and copies used collectors
 * to file server before it starts so the task can download them.
 *
 * @author Dan Kilman
 * @since 0.1
 */
@Configuration
public class DiamondProcessConfig {

    // ensure file server is started before diamond process is started
    @Inject
    private JettyFileServer jettyFileServer;

    // ensure worker is started before diamond process is started and closed after it
    @Inject
    private CeleryWorkerProcess celeryWorkerProcess;

    @Inject
    private TaskExecutor taskExecutor;

    @Inject
    private TemporaryDirectoryConfig.TemporaryDirectory temporaryDirectory;

    @NotEmpty
    @Value("${cosmo.test.file-server.temp-root}")
    private String fileServerTempRoot;

    @Bean(destroyMethod = "close")
    public DiamondProcess diamondProcess() throws Exception {
        File workdir = new File(temporaryDirectory.get(), "diamond");
        workdir.mkdir();
        copyCollectorsToFileServerDirectory();
        return new DiamondProcess(taskExecutor, buildJsonArgs(workdir));
    }

    private String buildJsonArgs(File workdir) throws JsonProcessingException {
        String user = System.getProperty("user.name");
        // TODO this is correct for me [dan]. not sure how to generally get this right
        // consider using diamond process flags: skip-change-user, skip-change-group
        String group = "users";
        Map<String, Object> map = ImmutableMap.<String, Object>builder()
            .put("diamond_config", ImmutableMap.builder()
                .put("skip_install_dependencies", "true")
                .put("skip_workaround", "true")
                .put("workdir", workdir.getAbsolutePath())
                .put("user", user)
                .put("group", group)
                .put("collectors_reload_interval", "3600")
                .put("riemann_host", "127.0.0.1")
                .put("riemann_port", "5555")
                .put("riemann_transport", "tcp")
                .put("collectors", buildCollectorsMap())
                .build())
            .build();
        return DSLProcessor.JSON_OBJECT_MAPPER.writeValueAsString(map);

    }

    private Map<Object, Object> buildCollectorsMap() {
        ImmutableMap.Builder<Object, Object> builder = ImmutableMap.builder()
            .put("celeryd", buildCollectorConfig(
                "http://localhost:53229/celeryd.py",
                "CeleryRegisteredTasksCollector",
                ImmutableMap.<String, Object>builder()
                    .put("path", "celeryd")
                    .put("broker_url", "amqp://")
                    .put("interval", "10")
                    .build()));

        return builder.build();
    }

    private Map<String, Object> buildCollectorConfig(String url, String name,
                                                     Map<String, Object> config) {
        return ImmutableMap.<String, Object>builder()
            .put("meta", ImmutableMap.builder()
                .put("url", url)
                .put("name", name)
                .build())
            .put("config", config)
            .build();
    }

    private void copyCollectorsToFileServerDirectory() {
        copyCollectorToFileServerDirectory(
                "diamond_collectors/celeryd/celeryd.py",
                "celeryd.py");
    }

    private void copyCollectorToFileServerDirectory(String resource,
                                                    String fileName) {
        File fileServerRoot = new File(temporaryDirectory.get(), fileServerTempRoot);
        final URL resourceUrl = Resources.getResource(resource);
        try {
            com.google.common.io.Files.copy(new InputSupplier<InputStream>() {
                @Override
                public InputStream getInput() throws IOException {
                    return resourceUrl.openStream();
                }
            }, new File(fileServerRoot, fileName));
        } catch (IOException e) {
            throw Throwables.propagate(e);
        }
    }
}
