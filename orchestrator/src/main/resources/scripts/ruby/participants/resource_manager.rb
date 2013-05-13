#/*******************************************************************************
# * Copyright (c) 2013 GigaSpaces Technologies Ltd. All rights reserved
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *       http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
# *******************************************************************************/

java_import org.cloudifysource.cosmo.resource.messages.CloudResourceMessage
java_import java.net.URI

class ResourceManagerParticipant < Ruote::Participant
  def on_workitem
    begin
      resource_id = workitem.fields['resource_id']
      action = workitem.params['action']
      producer = $ruote_properties['message_producer']
      resource_provisioner_topic = $ruote_properties['resource_provisioner_topic']

      $logger.debug('Resource provisioner participant invoked: [id={}, action={}, topic={}]',
                    resource_id,
                    action,
                    resource_provisioner_topic)

      raise 'resource_id is not set' unless defined? resource_id and not resource_id.nil?
      raise "unknown action '#{action}'" if action != 'start_machine'
      raise 'message_producer not defined' unless defined? producer
      raise 'resource_provisioner_topic not defined' unless defined? resource_provisioner_topic

      uri = URI.new(resource_provisioner_topic)
      message = CloudResourceMessage.new(resource_id, action)

      producer.send(uri, message).get()
      $logger.debug('Resource provisioner participant sent: [uri={}, message={}]', uri, message)

      reply
    end
  end
end

