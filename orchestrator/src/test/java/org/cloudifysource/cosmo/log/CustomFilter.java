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

package org.cloudifysource.cosmo.log;

import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.Marker;
import org.apache.logging.log4j.core.LogEvent;
import org.apache.logging.log4j.core.Logger;
import org.apache.logging.log4j.core.config.plugins.Plugin;
import org.apache.logging.log4j.core.config.plugins.PluginAttr;
import org.apache.logging.log4j.core.config.plugins.PluginFactory;
import org.apache.logging.log4j.core.filter.AbstractFilter;
import org.apache.logging.log4j.message.Message;

/**
* Log4j2 Filter.
*
* @author Dan Kilman
* @since 0.1
*/
@Plugin(name = "CustomFilter", type = "Core", elementType = "filter", printObject = true)
public class CustomFilter extends AbstractFilter {

    private final String[] stringArray;

    public CustomFilter(String[] stringArray) {
        super(Result.DENY, Result.ACCEPT);
        this.stringArray = stringArray;
    }

    @Override
    public Result filter(Logger logger, Level level, Marker marker, String msg, Object[] params) {
        return filter(msg);
    }

    @Override
    public Result filter(Logger logger, Level level, Marker marker, Object msg, Throwable t) {
        return filter(msg != null ? msg.toString() : "");
    }

    @Override
    public Result filter(Logger logger, Level level, Marker marker, Message msg, Throwable t) {
        return filter(msg != null ? msg.getFormattedMessage() : "");
    }

    @Override
    public Result filter(LogEvent event) {
        return filter(event.getMessage().getFormattedMessage());
    }

    private Result filter(String message) {
        if (message == null) {
            return onMatch;
        }
        for (String content : stringArray) {
            if (message.contains(content)) {
                return onMatch;
            }
        }
        return onMismatch;
    }

    @PluginFactory
    public static CustomFilter createFilter(@PluginAttr("content") final String content) {
        String[] stringArray = content.split(",");
        return new CustomFilter(stringArray);
    }

}
