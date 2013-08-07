###########################################################################
#
#      Author: Zachary Patten <zachary AT jovelabs DOT com>
#   Copyright: Copyright (c) Zachary Patten
#     License: Apache License, Version 2.0
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###########################################################################
#!/bin/bash

set -e

## lxc can't be installed on travis due to this error:
### invoke-rc.d: initscript lxc-net, action "start" failed
## the following workaround is via https://github.com/zpatten/lxc/blob/master/spec/support/install-lxc.sh
cat <<EOF | sudo tee /usr/sbin/policy-rc.d
#!/bin/sh
exit 101
EOF
sudo chmod 755 /usr/sbin/policy-rc.d
sudo apt-get -q -y install lxc
lxc-version