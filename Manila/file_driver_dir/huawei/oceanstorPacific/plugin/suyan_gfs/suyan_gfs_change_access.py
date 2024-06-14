# coding=utf-8
# Copyright (c) 2024 Huawei Technologies Co., Ltd.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log

from manila.i18n import _
from ..community.community_change_access import CommunityChangeAccess
from ...utils import constants

LOG = log.getLogger(__name__)


class SuyanGfsChangeAccess(CommunityChangeAccess):
    def __init__(self, client, share=None, driver_config=None,
                 context=None, storage_features=None):
        super(SuyanGfsChangeAccess, self).__init__(
            client, share, driver_config, context, storage_features)
        self.share_parent_id = self._get_share_parent_id()
        self.dtree_name = None
        self.dtree_id = None

    @staticmethod
    def get_impl_type():
        return constants.PLUGIN_SUYAN_GFS_IMPL

    def update_access(self, access_rules, add_rules, delete_rules):
        self._get_share_info()
        self._update_access_for_share(access_rules, add_rules, delete_rules)

    def allow_access(self, access):
        self._get_share_info()
        self._classify_rules([access], 'allow')

    def deny_access(self, access):
        self._get_share_info()
        self._classify_rules([access], 'deny')

    def _sync_access(self, access_rules):
        gfs_param = {
            'cluster_classification_name': self.storage_pool_name,
            'name': self.namespace_name,
            'is_remove_all': True
        }
        result = self.client.remove_ipaddress_from_gfs(gfs_param)
        self.client.wait_task_until_complete(result.get('task_id'))
        if 'DPC' in self.access_proto:
            self._classify_rules(access_rules, 'allow')

    def _get_share_info(self):
        """
        如果传入的参数包含parent_share_id，则走二级目录的流程
        """
        self._get_storage_pool_name()
        self._get_export_location_info()

        if not self.share_parent_id:
            self.namespace_name = 'share-' + self.share.get('share_id')
        else:
            self.namespace_name = 'share-' + self.share_parent_id

        self.access_proto = self._get_share_access_proto()

    def _deal_access_for_dpc(self, action):
        """
        allow or deny dpc ips for dpc gfs
        :param action: 'allow' or 'deny'
        :return:
        """
        dpc_access_ips_list = self._get_dpc_access_ips_list()

        for dpc_ips in dpc_access_ips_list:
            gfs_param = {
                'cluster_classification_name': self.storage_pool_name,
                'name': self.namespace_name,
                'ip_addresses': dpc_ips
            }
            if action == "allow":
                LOG.info("Will be add dpc access.(nums: {0})".format(len(dpc_ips)))
                result = self.client.add_ipaddress_to_gfs(gfs_param)
                self.client.wait_task_until_complete(result.get('task_id'))
            elif dpc_ips:
                LOG.info("Will be remove dpc access.(nums: {0})".format(len(dpc_ips)))
                result = self.client.remove_ipaddress_from_gfs(gfs_param)
                self.client.wait_task_until_complete(result.get('task_id'))