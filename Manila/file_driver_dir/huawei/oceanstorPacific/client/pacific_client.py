# coding=utf-8
# Copyright (c) 2021 Huawei Technologies Co., Ltd.
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
from oslo_serialization import jsonutils

from manila import exception
from manila.i18n import _

from .send_request import SendRequest
from ..utils import constants

LOG = log.getLogger(__name__)


class PacificClient(object):
    """Helper class for Huawei OceanStorPacific storage system."""

    def __init__(self, driver_config):
        self.send_request = SendRequest(driver_config)
        self.call = self.send_request.call

    @staticmethod
    def get_total_info_by_offset(func, extra_param):
        """
        Call the func interface cyclically to obtain the information in "data",
        combine it into a list and return it.
        which is used in the paging query interface
        """

        offset = 0
        total_info = []
        while True:
            result = func(offset, extra_param)
            data_info = result.get("data", [])
            total_info = total_info + data_info
            if len(data_info) < constants.MAX_QUERY_COUNT:
                break
            offset += constants.MAX_QUERY_COUNT
        return total_info

    @staticmethod
    def _is_needed_change_access(share_auth_info, access_to, access_value, access_param):
        if not share_auth_info:
            err_msg = _("Add an NFS shared client for share failed.(access_to: {0})".format(
                access_to))
            raise exception.InvalidShare(reason=err_msg)
        if share_auth_info[0].get(access_param) == access_value:
            LOG.info(_("Add an share client already exist.(access_to: {0})".format(
                access_to)))
            return False

        return True

    @staticmethod
    def _error_code(result):
        """Get error codes returned by all interfaces"""

        result_value = result.get('result')
        if isinstance(result_value, dict):
            error_code = result['result'].get("code")
        elif result_value == constants.DSWARE_SINGLE_ERROR:
            error_code = result.get("errorCode")
        else:
            error_code = result_value

        return error_code

    def login(self):
        result = self.call()
        return result.get('data', {})

    def logout(self):
        self.send_request.logout()

    def query_pool_info(self, pool_id=None):
        """This interface is used to query storage pools in a batch."""

        url = "data_service/storagepool"
        if pool_id:
            url += "?storagePoolId={0}".format(pool_id)
        result = self.call(url, None, "GET")

        if result.get('result') == 0 and result.get("storagePools"):
            LOG.debug("Query storage pool success.(pool_id: {0}) ".format(pool_id))
        else:
            err_msg = "Query storage pool failed.(pool_id: {0})".format(pool_id)
            raise exception.InvalidShare(reason=err_msg)

        return result.get('storagePools', [])

    def query_system_capacity(self):
        """query system capacity to get ssd、sata capacity"""

        url = "system_capacity"
        result = self.call(url, None, "GET")
        self._assert_result(result, "Query system capacity failed.")
        return result.get('data', {})

    def query_account_by_name(self, account_name):
        """This interface is used to query an account."""

        url = "account/accounts"
        query_para = {
            'name': account_name
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")

        result_data = result.get("data")
        if result.get('result', {}).get('code') == 0 and result_data:
            LOG.info(_("Query account name success.(account_name: {0})".format(account_name)))
        elif result.get('result', {}).get('code') == constants.ACCOUNT_NOT_EXIST and not result_data:
            LOG.info(_("Query account name does not exist.(account_name: {0})".format(account_name)))
        else:
            err_msg = _("Query account name({0}) failed".format(account_name))
            raise exception.InvalidShare(reason=err_msg)

        return result_data

    def create_account(self, account_name):
        """This interface is used to create an account."""

        url = "account/accounts"
        account_para = {
            'name': account_name
        }
        data = jsonutils.dumps(account_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get("data"):
            LOG.info(_("Create account success.(account_name: {0})".format(account_name)))
        else:
            err_msg = _("Create account failed.(account_name: {0})".format(account_name))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data')

    def delete_account(self, account_id):
        """This interface is used to delete an account."""

        url = "account/accounts"
        account_para = {
            'id': account_id
        }
        data = jsonutils.dumps(account_para)
        result = self.call(url, data, "DELETE")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete account success.(account_id: {0})".format(account_id)))
        else:
            err_msg = (_("Delete account failed.(account_id: {0})".format(account_id)))
            raise exception.InvalidShare(reason=err_msg)

    def query_access_zone_count(self, account_id):

        url = "eds_dns_service/zone_count?account_id={0}".format(account_id)
        result = self.call(url, None, "GET")

        if result.get('result', {}).get('code') == 0 and result.get("data"):
            LOG.info(_("Query account access zone success.(account_id: {0})".format(account_id)))
        else:
            err_msg = _("Query account access zone failed.(account_id: {0})".format(account_id))
            raise exception.InvalidShare(reason=err_msg)

        return result.get("data")

    def query_namespaces_count(self, account_id):
        """This interface is used to query the number of configured namespaces."""

        url = "converged_service/namespaces_count"
        query_para = {
            'filter': {'account_id': account_id}
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0 and result.get("data"):
            LOG.info(_("Query namespace quantity of account success.(account_id :{0})".format(account_id)))
        else:
            err_msg = _("Query namespace quantity of account failed.(account_id :{0})".format(account_id))
            raise exception.InvalidShare(reason=err_msg)

        return result.get("data")

    def query_namespace_by_name(self, namespace_name):
        """Query the configurations of a namespace based on its name"""

        url = "converged_service/namespaces"
        query_para = {
            'name': namespace_name
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")

        result_data = result.get("data")
        if result.get('result', {}).get('code') == 0 and result_data:
            LOG.info(_("Query namespace success.(namespace_name: {0})".format(namespace_name)))
        elif result.get('result', {}).get('code') == constants.NAMESPACE_NOT_EXIST and not result_data:
            LOG.info(_("Query namespace does not exist.(namespace_name: {0})".format(namespace_name)))
        else:
            err_msg = _("Query namespace({0}) failed".format(namespace_name))
            raise exception.InvalidShare(reason=err_msg)

        return result_data

    def create_namespace(self, namespace_param):
        """This interface is used to create a namespace."""

        url = "converged_service/namespaces"
        namespace_name = namespace_param.get('name')
        data = jsonutils.dumps(namespace_param)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get("data"):
            LOG.info(_("Create namespace success.(namespace_name {0})".format(namespace_name)))
        else:
            err_msg = _("Create namespace failed.(namespace_name {0})".format(namespace_name))
            raise exception.InvalidShare(reason=err_msg)

        return result.get("data")

    def delete_namespace(self, namespace_name):
        """This interface is used to delete a namespace based on its name."""

        url = "converged_service/namespaces"
        namespace_para = {
            'name': namespace_name
        }
        data = jsonutils.dumps(namespace_para)
        result = self.call(url, data, "DELETE")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete namespace success.(namespace_name: {0})".format(namespace_name)))
        elif result.get('result', {}).get('code') == constants.NAMESPACE_NOT_EXIST:
            LOG.info(_("Delete namespace does not exist.(namespace_name: {0})".format(namespace_name)))
        else:
            err_msg = (_("Delete namespace({0}) failed.".format(namespace_name)))
            raise exception.InvalidShare(reason=err_msg)

    def query_quota_by_parent(self, parent_id, parent_type):
        """This interface is used to query namespace quotas in batches."""

        url = "converged_service/quota"
        query_para = {
            "parent_type": parent_type,
            "parent_id": parent_id,
            "space_unit_type": constants.QUOTA_UNIT_TYPE_BYTES,
            "range": "{\"offset\": 0, \"limit\": 10}"
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query quota success.(parent_id: {0})".format(parent_id)))
        else:
            err_msg = _("Query quota  failed.(parent_id: {0})".format(parent_id))
            raise exception.InvalidShare(reason=err_msg)

        if not result.get("data"):
            return {}
        return result.get("data")[0]

    def creat_quota(self, namespace_id, quota_size, quota_type):
        """This interface is used to create a namespace quota."""

        url = "converged_service/quota"
        quota_para = {
            "parent_type": quota_type,
            "parent_id": namespace_id,
            "quota_type": constants.QUOTA_TYPE_DIRECTORY,
            "space_hard_quota": quota_size,
            "space_unit_type": constants.QUOTA_UNIT_TYPE_GB,
            "directory_quota_target": constants.QUOTA_TARGET_NAMESPACE
        }
        data = jsonutils.dumps(quota_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get("data"):
            LOG.info(_("Create quota success. (quota_size: {0}GB)".format(quota_size)))
        else:
            err_msg = _("Create quota failed.")
            raise exception.InvalidShare(reason=err_msg)

    def change_quota_size(self, quota_id, new_size):
        """This interface is used to modify a namespace quota."""

        url = "converged_service/quota"
        quota_para = {
            "id": quota_id,
            "space_hard_quota": new_size,
            "space_unit_type": constants.QUOTA_UNIT_TYPE_GB
        }
        data = jsonutils.dumps(quota_para)
        result = self.call(url, data, "PUT")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Change quota success.(quota_size: {0}GB)".format(new_size)))
        else:
            err_msg = _("Change quota failed")
            raise exception.InvalidShare(reason=err_msg)

    def create_qos(self, qos_name, account_id, qos_config):
        """This interface is used to create a converged QoS policy."""

        url = "dros_service/converged_qos_policy"
        qos_para = {
            'name': qos_name,
            'qos_mode': constants.QOS_MODE_PACKAGE,
            'qos_scale': constants.QOS_SCALE_NAMESPACE,
            'account_id': account_id,
            'package_size': 10,
            'max_band_width': qos_config['max_band_width'],
            'basic_band_width': qos_config['basic_band_width'],
            'bps_density': qos_config['bps_density'],
            'max_iops': qos_config['max_iops']
        }
        data = jsonutils.dumps(qos_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get("data"):
            LOG.info(_("Create qos success.(qos_name: {0})".format(qos_name)))
        else:
            err_msg = _("Create qos failed.(qos_name: {0})".format(qos_name))
            raise exception.InvalidShare(reason=err_msg)

        return result.get("data")

    def add_qos_association(self, namespace_name, qos_policy_id, account_id):
        """This interface is used to add a converged QoS policy association."""

        url = "dros_service/converged_qos_association"
        qos_asso_para = {
            'qos_scale': constants.QOS_SCALE_NAMESPACE,
            'object_name': namespace_name,
            'qos_policy_id': qos_policy_id,
            'account_id': account_id
        }
        data = jsonutils.dumps(qos_asso_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Add a QoS policy association success."))
        else:
            err_msg = _("Add a QoS policy association failed.")
            raise exception.InvalidShare(reason=err_msg)

    def delete_qos(self, qos_name):
        """This interface is used to delete a converged QoS policy."""

        url = "dros_service/converged_qos_policy"
        qos_para = {
            'name': qos_name,
            'qos_scale': 0
        }
        data = jsonutils.dumps(qos_para)
        result = self.call(url, data, "DELETE")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete the qos success.(qos_name: {0})".format(qos_name)))
        elif result.get('result', {}).get('code') == constants.QOS_NOT_EXIST:
            LOG.info(_("Delete the qos does not exist.(qos_name: {0})".format(qos_name)))
        else:
            err_msg = "Delete the qos failed.(qos_name: {0})".format(qos_name)
            raise exception.InvalidShare(reason=err_msg)

    def query_tier_migrate_policies_by_name(self, name):
        url = "tier_service/tier_migrate_policies"
        params = {
            "filter": {'name': name}
        }
        data = jsonutils.dumps(params)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query tier migrate policies by name success.(tier_name: {0})".format(name)))
        else:
            err_msg = _("Query tier migrate policies by name failed.(tier_name: {0})".format(name))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data', [])

    def query_tier_grade_policies_by_name(self, name):
        url = "tier_service/tier_placement_policies"
        params = {
            "filter": {'name': name}
        }
        data = jsonutils.dumps(params)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query tier grade policies by name success.(tier_name: {0})".format(name)))
        else:
            err_msg = _("Query tier grade policies by name failed.(tier_name: {0})".format(name))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data', [])

    def create_tier_grade_policy(self, tier_grade_param):
        """This interface is used to create the placement policy."""

        url = "tier_service/tier_placement_policies"
        data = jsonutils.dumps(tier_grade_param)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Create tier grade policy success.(tier_name: {0})"
                       "".format(tier_grade_param.get('name'))))
        else:
            err_msg = _("Create tier grade policy failed.(tier_name: {0})"
                        "".format(tier_grade_param.get('name')))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data')

    def create_tier_migrate_policy(self, tier_migrate_param):
        """This interface is used to create the migration policy."""

        url = "tier_service/tier_migrate_policies"
        data = jsonutils.dumps(tier_migrate_param)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Create tier migrate policy success.(tier_name: {0})"
                       "".format(tier_migrate_param.get('name'))))
            result['error_code'] = 0
        elif result.get('result', {}).get('code') == constants.PATH_NOT_EXIST:
            LOG.warning("Create tier migrate policy failed, the file_path:%s is not "
                        "correct", tier_migrate_param.get("path_name"))
            result['error_code'] = 1
        else:
            err_msg = _("Create tier migrate policy failed.(tier_name: {0})"
                        .format(tier_migrate_param.get('name')))
            raise exception.InvalidShare(reason=err_msg)
        return result

    def create_nfs_share(self, namespace_name, account_id):
        """This interface is used to create an NFS share."""

        url = "nas_protocol/nfs_share"
        nfs_para = {
            'share_path': '/' + namespace_name,
            'account_id': account_id
        }
        data = jsonutils.dumps(nfs_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get('data'):
            LOG.info(_("Create NFS share success.(namespace_name: {0})".format(namespace_name)))
        else:
            err_msg = _("Create NFS share failed.(namespace_name: {0})".format(namespace_name))
            raise exception.InvalidShare(reason=err_msg)

    def create_cifs_share(self, namespace_name, account_id):
        """This interface is used to create a CIFS share."""

        url = "file_service/cifs_share"
        cifs_param = {
            "name": namespace_name,
            "share_path": '/' + namespace_name,
            "account_id": account_id,
        }

        data = jsonutils.dumps(cifs_param)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get('data'):
            LOG.info(_("Create CIFS share success.(namespace_name: {0})".format(namespace_name)))
        else:
            err_msg = _("Create CIFS share failed.(namespace_name: {0})".format(namespace_name))
            raise exception.InvalidShare(reason=err_msg)

    def query_nfs_share_information(self, account_id, fs_id, dtree_id=0):
        """This interface is used to batch query NFS share information."""

        url = "nas_protocol/nfs_share_list"
        nfs_para = {
            "account_id": account_id,
            "filter": "[{\"fs_id\": %d, \"dtree_id\": \"%s\"}]" %
                      (fs_id, str(dtree_id))
        }
        data = jsonutils.dumps(nfs_para)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query NFS share success.(account_id: {0})".format(account_id)))
        else:
            err_msg = _("Query NFS share failed.(account_id: {0})".format(account_id))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data')

    def query_cifs_share_information(self, account_id, share_name):
        """This interface is used to batch query basic information about CIFS shares."""

        url = "file_service/cifs_share_list"

        cifs_para = {
            "account_id": account_id,
            "filter": "[{\"name\":\"%s\"}]" % share_name
        }

        data = jsonutils.dumps(cifs_para)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query CIFS share success.(account_id: {0})".format(account_id)))
        else:
            err_msg = _("Query CIFS share failed.(account_id: {0})".format(account_id))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data')

    def delete_nfs_share(self, nfs_share_id, account_id):
        """This interface is used to delete an NFS share."""

        url = "nas_protocol/nfs_share"
        nfs_para = {
            'id': nfs_share_id,
            'account_id': account_id
        }
        data = jsonutils.dumps(nfs_para)
        result = self.call(url, data, "DELETE")
        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete the NFS share success.(nfs_share_id: {0})".format(nfs_share_id)))
        else:
            err_msg = "Delete the NFS share failed.(nfs_share_id: {0})".format(nfs_share_id)
            raise exception.InvalidShare(reason=err_msg)

    def delete_cifs_share(self, cifs_share_id, account_id):
        """This interface is used to delete a CIFS share."""

        url = "file_service/cifs_share"
        cifs_para = {
            "id": cifs_share_id,
            "account_id": account_id
        }
        data = jsonutils.dumps(cifs_para)
        result = self.call(url, data, "DELETE")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete the CIFS share success.(cifs_share_id: {0})".format(cifs_share_id)))
        else:
            err_msg = "Delete the CIFS share failed.(cifs_share_id: {0})".format(cifs_share_id)
            raise exception.InvalidShare(reason=err_msg)

    def query_users_by_id(self, account_id):
        """This interface is used to query basic information about a UNIX user."""

        url = "nas_protocol/unix_user?account_id={0}".format(account_id)
        result = self.call(url, None, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query users success.(account_id: {0})".format(account_id)))
        else:
            err_msg = _("Query users failed.(account_id: {0})".format(account_id))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data')

    def query_user_groups_by_id(self, account_id):
        """This interface is used to query basic information about a UNIX user group."""

        url = "nas_protocol/unix_group?account_id={0}".format(account_id)
        result = self.call(url, None, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query users groups success.(account_id: {0})".format(account_id)))
        else:
            err_msg = _("Query users groups failed.(account_id: {0})".format(account_id))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data')

    def delete_unix_user(self, user_name, account_id):
        """This interface is used to delete a UNIX user."""

        url = "nas_protocol/unix_user?name={0}&account_id={1}".format(user_name, account_id)
        result = self.call(url, None, "DELETE")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete the user success.(user_name: {0})".format(user_name)))
        else:
            err_msg = _("Delete the user failed.(user_name: {0})".format(user_name))
            raise exception.InvalidShare(reason=err_msg)

    def delete_unix_user_group(self, group_name, account_id):
        """This interface is used to delete a UNIX user group."""

        url = "nas_protocol/unix_group?name={0}&account_id={1}".format(group_name, account_id)
        result = self.call(url, None, "DELETE")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete the user group success.(group_name: {0})".format(group_name)))
        else:
            err_msg = _("Delete the user group failed.(group_name: {0})".format(group_name))
            raise exception.InvalidShare(reason=err_msg)

    def allow_access_for_nfs(self, share_id, access_to, access_level, account_id):
        """This interface is used to add an NFS share client."""

        access_value = 0 if access_level == 'ro' else 1
        url = "nas_protocol/nfs_share_auth_client"
        access_para = {
            'access_name': access_to,
            'share_id': share_id,
            'access_value': access_value,
            'sync': 1,
            'all_squash': 1,
            'root_squash': 1,
            'account_id': account_id,
        }

        data = jsonutils.dumps(access_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Add an NFS share client success.(access_to: {0})".format(access_to)))
        elif result.get('result', {}).get('code') == constants.NFS_SHARE_CLIENT_EXIST:
            share_auth_info = self._query_nfs_share_clients_information(
                0, [share_id, account_id], access_to).get('data', [])
            if self._is_needed_change_access(share_auth_info, access_to, access_value, 'access_value'):
                self.change_access_for_nfs(
                    share_auth_info[0].get('id'), access_value, account_id)
        else:
            err_msg = _("Add an NFS shared client for share failed.(access_to: {0})".format(share_id))
            raise exception.InvalidShare(reason=err_msg)

    def change_access_for_nfs(self, client_id, access_value, account_id):
        """This interface is used to change a CIFS share auth client access_value."""
        url = "nas_protocol/nfs_share_auth_client"
        access_para = {
            'id': client_id,
            'access_value': access_value,
            'sync': 1,
            'all_squash': 1,
            'root_squash': 1,
            'account_id': account_id,
        }
        data = jsonutils.dumps(access_para)
        result = self.call(url, data, "PUT")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("change an NFS share client success.(client id: {0})".format(client_id)))
        else:
            err_msg = _("change an NFS shared client for share failed.(client id: {0})".
                        format(client_id))
            raise exception.InvalidShare(reason=err_msg)
        return result

    def allow_access_for_cifs(self, share_id, access_to, access_level, account_id):
        """This interface is used to add a CIFS share user or user group."""

        url = "file_service/cifs_share_auth_client"
        access_value = 0 if access_level == 'ro' else 1
        query_para = {
            "share_id": share_id,
            "name": access_to,
            "domain_type": 2,
            "permission": access_value,
            "account_id": account_id
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Add an CIFS share user success.(access_to: {0})".format(access_to)))
        elif result.get('result', {}).get('code') == constants.CIFS_SHARE_CLIENT_EXIST:
            share_auth_info = self._query_cifs_share_user_information(
                0, [share_id, account_id], access_to).get('data', [])
            if self._is_needed_change_access(share_auth_info, access_to,
                                             access_value, 'permission'):
                self.change_access_for_cifs(
                    share_auth_info[0].get('id'), access_value, account_id)
        else:
            err_msg = _("Add an CIFS shared client for share failed.(access_to: {0})".format(share_id))
            raise exception.InvalidShare(reason=err_msg)

    def change_access_for_cifs(self, client_id, access_value, account_id):
        """This interface is used to change a CIFS share auth client permission."""
        url = "file_service/cifs_share_auth_client"
        access_para = {
            "id": client_id,
            "permission": access_value,
            "account_id": account_id
        }
        data = jsonutils.dumps(access_para)
        result = self.call(url, data, "PUT")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("change an CIFS share client success.(client id: {0})".format(
                client_id)))
        else:
            err_msg = _("change an CIFS shared client for share failed.(client id: {0})".
                        format(client_id))
            raise exception.InvalidShare(reason=err_msg)
        return result

    def query_nfs_share_clients_information(self, share_id, account_id=None):
        totals = self.get_total_info_by_offset(
            self._query_nfs_share_clients_information, [share_id, account_id])
        return totals

    def query_cifs_share_user_information(self, share_id, account_id=None):
        totals = self.get_total_info_by_offset(
            self._query_cifs_share_user_information, [share_id, account_id])
        return totals

    def deny_access_for_nfs(self, client_id, account_id):
        """This interface is used to delete an NFS share client."""

        url = "nas_protocol/nfs_share_auth_client"

        nfs_para = {
            'id': client_id,
            'account_id': account_id
        }
        data = jsonutils.dumps(nfs_para)
        result = self.call(url, data, "DELETE")
        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete the NFS client success.(client_id: {0})".format(client_id)))
        else:
            err_msg = "Delete the NFS client failed.(client_id: {0})".format(client_id)
            raise exception.InvalidShare(reason=err_msg)

    def deny_access_for_cifs(self, user_id, account_id):
        """This interface is used to delete a CIFS share user or user group."""

        url = "file_service/cifs_share_auth_client"
        query_para = {
            "id": user_id,
            "account_id": account_id
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "DELETE")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Delete the CIFS client success.(user_id: {0})".format(user_id)))
        else:
            err_msg = "Delete the CIFS client failed.(user_id: {0})".format(user_id)
            raise exception.InvalidShare(reason=err_msg)

    def open_dpc_auth_switch(self, namespace_name):
        """	Enable or disable DPC authentication."""

        url = "/dsware/service/fsmCliCmd"
        auth_para = {
            "namespace": namespace_name,
            "auth_type": "DPC_AUTH_IP",
            "switch": "DPC_AUTH_SWITCH_ON",
            "name": "setDpcAuthSwitch",
            "serviceType": "eds-f"
        }

        data = jsonutils.dumps(auth_para)
        result = self.call(None, data, "POST", ex_url=url)
        if result.get('result') == 0:
            LOG.info(_("Open DPC Auth switch success.(namespace_name: {0})".format(namespace_name)))
        else:
            err_msg = _("Open DPC Auth switch failed.(namespace_name: {0})".format(namespace_name))
            raise exception.InvalidShare(reason=err_msg)

    def allow_access_for_dpc(self, namespace_name, dpc_ip):
        """Create DPC authentication information."""

        url = "/dsware/service/fsmCliCmd"
        access_para = {
            "ip": dpc_ip,
            "namespace": namespace_name,
            "auth_type": "DPC_AUTH_IP",
            "name": "setDpcIpAuth",
            "serviceType": "eds-f"
        }

        data = jsonutils.dumps(access_para)
        result = self.call(None, data, "POST", ex_url=url)

        nums = len(dpc_ip.split(','))
        if result.get('result') == 0:
            LOG.info(_("Add DPC Auth access success.(namespace_name:{0} nums:{1})".format(namespace_name, nums)))
        else:
            err_msg = _("Add DPC Auth access failed.(namespace_name:{0} nums:{1})".format(namespace_name, nums))
            raise exception.InvalidShare(reason=err_msg)

    def deny_access_for_dpc(self, namespace_name, dpc_ip):
        """	Delete DPC authentication information."""

        url = "/dsware/service/fsmCliCmd"
        access_para = {
            "ip": dpc_ip,
            "namespace": namespace_name,
            "auth_type": "DPC_AUTH_IP",
            "name": "delDpcIpAuth",
            "serviceType": "eds-f"
        }

        data = jsonutils.dumps(access_para)
        result = self.call(None, data, "POST", ex_url=url)

        nums = len(dpc_ip.split(','))
        if result.get('result') == 0:
            LOG.info(_("Delete DPC Auth access success.(namespace_name:{0} nums:{1})".format(namespace_name, nums)))
        else:
            err_msg = _("Delete DPC Auth access failed.(namespace_name:{0} nums:{1})".format(namespace_name, nums))
            raise exception.InvalidShare(reason=err_msg)

    def get_all_namespace_info(self, account_id):
        """Get all namespace information"""

        totals = self.get_total_info_by_offset(
            self._get_namespace_info, [account_id])
        return totals

    def query_qos_info_by_name(self, qos_name):
        """Get qos information through qos name"""

        url = 'dros_service/converged_qos_policy'
        query_para = {
            "qos_scale": constants.QOS_SCALE_NAMESPACE,
            "name": qos_name
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")
        self._assert_result(result, 'Query qos info by qos_name error.')
        return result

    def create_qos_for_suyan(self, qos_name, account_id, qos_config):
        """Used to create a converged QoS policy for suyan."""

        url = "dros_service/converged_qos_policy"
        qos_para = {
            'name': qos_name,
            'qos_mode': constants.QOS_MODE_MANUAL,
            'qos_scale': constants.QOS_SCALE_NAMESPACE,
            'account_id': account_id,
            'max_mbps': qos_config['max_band_width'],
            'max_iops': qos_config['max_iops'],
        }
        data = jsonutils.dumps(qos_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get('data'):
            LOG.info(_("Create qos for suyan success.(qos_name: {0})".format(qos_name)))
        else:
            err_msg = _("Create qos for suyan failed.(qos_name: {0})".format(qos_name))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data')

    def change_qos_for_suyan(self, qos_name, account_id, qos_config):
        """Modify qos parameters"""

        url = "dros_service/converged_qos_policy"
        qos_para = {
            'name': qos_name,
            'qos_mode': constants.QOS_MODE_MANUAL,
            'qos_scale': constants.QOS_SCALE_NAMESPACE,
            'account_id': account_id,
            'max_mbps': qos_config['max_band_width'],
            'max_iops': qos_config['max_iops'],
        }
        data = jsonutils.dumps(qos_para)
        result = self.call(url, data, "PUT")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Change qos for suyan success.(qos_name: {0})".format(qos_name)))
        else:
            err_msg = _("Change qos for suyan failed.(qos_name: {0})".format(qos_name))
            raise exception.InvalidShare(reason=err_msg)

        return

    def create_dtree(self, dtree_name, namespace_name):
        """create dtree by namespace name"""

        url = "file_service/dtrees"
        dtree_params = {
            'name': dtree_name,
            'file_system_name': namespace_name
        }
        data = jsonutils.dumps(dtree_params)
        result = self.call(url, data, 'POST')

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Create dtree of namespace success.(dtree_name: {0},"
                       " namespace_name: {1})".format(dtree_name, namespace_name)))
        else:
            err_msg = _("Create dtree of namespace failed.(dtree_name: {0},"
                        " namespace_name: {1})".format(dtree_name, namespace_name))
            raise exception.InvalidShare(reason=err_msg)
        return result.get('data')

    def delete_dtree(self, dtree_name, namespace_name):
        """delete dtree by dtree name and namespace_name"""
        url = "file_service/dtrees?name={0}&file_system_name={1}".format(
            dtree_name, namespace_name)
        result = self.call(url, None, "DELETE")

        result_code = result.get('result', {}).get('code')
        if result_code == 0:
            LOG.info(_("Delete dtree of namespace success."
                       "(dtree_name: {0}, namespace_name: {1})".
                       format(dtree_name, namespace_name)))
        elif result_code == constants.NAMESPACE_NOT_EXIST:
            LOG.info(_("theparent namespace {1}  of dtree {0} does not exist."
                       "(dtree_name: {0},  namespace_name: {1})".
                       format(namespace_name, dtree_name)))
        elif result_code == constants.DTREE_NOT_EXIST:
            LOG.info(_("the dtree {0} of namespace {1} does not exist."
                       "(dtree_name: {0}, namespace_name: {1})".
                       format(dtree_name, namespace_name)))
        else:
            err_msg = _("Delete dtree of namespace failed.(dtree_name: {0}, "
                        "namespace_name: {1})".format(dtree_name, namespace_name))
            raise exception.InvalidShare(reason=err_msg)

    def create_dtree_nfs_share(self, namespace_name, dtree_name, account_id):
        """This interface is to create dtree nfs share"""
        url = "nas_protocol/nfs_share"
        nfs_para = {
            'share_path': '/' + namespace_name + '/' + dtree_name,
            'account_id': account_id
        }
        data = jsonutils.dumps(nfs_para)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get('data'):
            LOG.info(_("Create Dtree NFS share success."
                       "(namespace_name: {0}, dtree_name: {1})".format(namespace_name, dtree_name)))
        else:
            err_msg = _("Create Dtree NFS share failed."
                        "(namespace_name: {0}, dtree_name: {1})".format(namespace_name, dtree_name))
            raise exception.InvalidShare(reason=err_msg)

    def create_dtree_cifs_share(self, namespace_name, dtree_name, account_id):
        """This interface is used to create a CIFS share."""

        url = "file_service/cifs_share"
        cifs_param = {
            "name": dtree_name,
            "share_path": '/' + namespace_name + '/' + dtree_name,
            "account_id": account_id,
        }

        data = jsonutils.dumps(cifs_param)
        result = self.call(url, data, "POST")

        if result.get('result', {}).get('code') == 0 and result.get('data'):
            LOG.info(_("Create Dtree CIFS share success."
                       "(namespace_name: {0}, dtree_name: {1})".format(namespace_name, dtree_name)))
        else:
            err_msg = _("Create Dtree CIFS share failed."
                        "(namespace_name: {0}, dtree_name: {1})".format(namespace_name, dtree_name))
            raise exception.InvalidShare(reason=err_msg)

    def query_dtree_by_name(self, dtree_name, namespace_id):
        """Query the configurations of a namespace based on its name"""

        url = "file_service/dtrees"
        query_para = {
            'file_system_id': namespace_id,
            'filter': {'name': dtree_name}
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query dtree success.(dtree_name: {0})".format(dtree_name)))
        elif result.get('result', {}).get('code') == constants.DTREE_NOT_EXIST or not \
                result.get('data'):
            LOG.info(_("Query dtree does not exist.(dtree_name: {0})".format(dtree_name)))
        else:
            err_msg = _("Query dtree_name({0}) failed".format(dtree_name))
            raise exception.InvalidShare(reason=err_msg)

        return result.get('data', [])

    def get_all_dtree_info_of_namespace(self, filesystem_id):
        """Get all dtree information of one namespace"""

        totals = self.get_total_info_by_offset(
            self._get_all_dtree_info_of_namespace, [filesystem_id])
        return totals

    def query_disk_pool_by_storagepool_id(self, storagepool_id):
        """
        query all disk pool info of a storagepool
        :param storagepool_id: storage pool id
        :return: all disk pool info
        """
        url = 'data_service/diskpool'
        query_param = {
            'storagePoolId': storagepool_id
        }
        data = jsonutils.dumps(query_param)
        result = self.call(url, data, "GET")
        self._assert_result(result, 'Query disk pool info error.')
        return result.get('diskPools', [])

    def query_tier_global_cfg(self):
        """
        query storage tier_global_cfg
        :return: storage tier_global_cfg
        """
        url = 'hdfs_tier_service/tier_global_cfg'
        result = self.call(url, method='GET')
        self._assert_result(result, 'Query storage tier global cfg failed')
        return result.get('data')

    def modify_tier_grade_policy_by_id(self, tier_id, strategy, account_id):
        url = 'tier_service/tier_placement_policies/{0}'.format(tier_id)
        param = {
            'strategy': strategy,
            'account_id': account_id
        }
        data = jsonutils.dumps(param)
        result = self.call(url, data, "PUT")
        self._assert_result(result, "Modify tier grade policy failed")

    def delete_tier_grade_policy_by_id(self, tier_id, account_id):
        url = 'tier_service/tier_placement_policies/{0}'.format(tier_id)
        param = {
            'account_id': account_id
        }
        data = jsonutils.dumps(param)
        result = self.call(url, data, "DELETE")
        result_code = result.get('result', {}).get('code')
        if result_code == 0:
            LOG.info("Delete tier placement policy successfully,"
                     " tier id is %s", tier_id)
        elif result_code == constants.TIER_POLICY_NOT_EXIST:
            LOG.info("Tier placement policy %s not exist, skip it", tier_id)
        else:
            err_msg = ("Delete tier placement policy failed.tier_id is %s" % tier_id)
            LOG.error(err_msg)
            raise exception.InvalidShare(reason=err_msg)

    def modify_tier_migrate_policy_by_id(self, tier_id, strategy, atime, account_id):
        url = 'tier_service/tier_migrate_policies/{0}'.format(tier_id)
        param = {
            'strategy': strategy,
            'atime_operator': constants.MATCH_RULE_GT,
            'atime': atime,
            'atime_unit': constants.HTIME_UNIT,
            'account_id': account_id
        }
        data = jsonutils.dumps(param)
        result = self.call(url, data, "PUT")
        self._assert_result(result, "Modify tier migrate policy failed")

    def delete_tier_migrate_policy_by_id(self, tier_id, account_id):
        url = 'tier_service/tier_migrate_policies/{0}'.format(tier_id)
        param = {
            'account_id': account_id
        }
        data = jsonutils.dumps(param)
        result = self.call(url, data, "DELETE")
        result_code = result.get('result', {}).get('code')
        if result_code == 0:
            LOG.info("Delete tier migrate policy successfully,"
                     " tier id is %s", tier_id)
        elif result_code == constants.TIER_POLICY_NOT_EXIST:
            LOG.info("Tier migrate policy %s not exist, skip it", tier_id)
        else:
            err_msg = ("Delete tier migrate policy failed.tier_name is %s" % tier_id)
            LOG.error(err_msg)
            raise exception.InvalidShare(reason=err_msg)

    def delete_tier_grade_policy_by_name(self, tier_name, namespace_id, account_id):
        """
        delete tier grade policy by name
        :param tier_name: tier name to be deleted
        :param namespace_id: the id of namespace which tier associate
        :return: None
        """
        url = 'tier_service/tier_placement_policies'
        param = {
            'name': tier_name,
            'fs_id': namespace_id,
            'account_id': account_id
        }
        data = jsonutils.dumps(param)
        result = self.call(url, data, "DELETE")
        result_code = result.get('result', {}).get('code')
        if result_code == 0:
            LOG.info("Delete tier placement policy successfully,"
                     " tier name is %s", tier_name)
        elif result_code == constants.TIER_POLICY_NOT_EXIST:
            LOG.info("Tier placement policy %s not exist, skip it", tier_name)
        else:
            err_msg = ("Delete tier placement policy failed.tier_name is %s" % tier_name)
            LOG.error(err_msg)
            raise exception.InvalidShare(reason=err_msg)

    def delete_tier_migrate_policy_by_name(self, tier_name, namespace_id, account_id):
        """
        delete tier migrate policy by name
        :param tier_name: tier name to be deleted
        :param namespace_id: the id of namespace which tier associate
        :return: None
        """
        url = 'tier_service/tier_migrate_policies'
        param = {
            'name': tier_name,
            'fs_id': namespace_id,
            'account_id': account_id
        }
        data = jsonutils.dumps(param)
        result = self.call(url, data, "DELETE")
        result_code = result.get('result', {}).get('code')
        if result_code == 0:
            LOG.info("Delete tier migrate policy successfully,"
                     " tier name is %s", tier_name)
        elif result_code == constants.TIER_POLICY_NOT_EXIST:
            LOG.info("Tier migrate policy %s not exist, skip it", tier_name)
        else:
            err_msg = ("Delete tier migrate policy failed.tier_name is %s" % tier_name)
            LOG.error(err_msg)
            raise exception.InvalidShare(reason=err_msg)

    def change_namespace_info(self, update_param):
        """
        update namespace info
        :param update_param: the param need to be udpate
        :return:
        """
        url = 'converged_service/namespaces'
        data = jsonutils.dumps(update_param)
        result = self.call(url, data, "PUT")
        self._assert_result(result, 'Query storage tier global cfg failed')

    def get_esn(self):
        """
        Get the cluster ESN.
        :return:
        """
        url = 'common/esn'
        result = self.call(url, method="GET")
        self._assert_result(result, 'Query storage tier global cfg failed')
        return result.get('data', {}).get('esn')

    def _assert_result(self, result, msg_format, *args):
        """Determine error codes, print logs and report errors"""

        if self._error_code(result) != 0:
            args += (result,)
            msg = (msg_format + '\nresult: %s.') % args
            LOG.error(msg)
            raise exception.InvalidShare(msg)

    def _get_namespace_info(self, offset, extra_param):
        """Get namespace information in batches"""

        url = 'converged_service/namespaces'
        query_para = {
            "range": {"offset": offset,
                      "limit": constants.MAX_QUERY_COUNT},
            "filter": {"account_id": extra_param[0]}
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")
        self._assert_result(result, 'Batch query namespaces info error.')
        return result

    def _query_cifs_share_user_information(self, offset, extra_param, access_name=None):
        """This interface is used to query CIFS share users or user groups in batches."""

        url = "file_service/cifs_share_auth_client_list"
        if access_name is not None:
            filter_str = "[{\"share_id\": \"%s\", \"name\": \"like %s\"}]" % (
                str(extra_param[0]), access_name)
        else:
            filter_str = "[{\"share_id\": \"%s\"}]" % str(extra_param[0])
        filter_para = {
            "filter": filter_str,
            "range": {
                "offset": offset,
                "limit": constants.MAX_QUERY_COUNT
            },
            "account_id": extra_param[1],
        }

        data = jsonutils.dumps(filter_para)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query CIFS share user success.(cifs_share_id: {0})".format(extra_param[0])))
        else:
            err_msg = _("Query CIFS share user failed.(cifs_share_id: {0})".format(extra_param[0]))
            raise exception.InvalidShare(reason=err_msg)

        return result

    def _query_nfs_share_clients_information(self, offset, extra_param, access_name=None):
        """This interface is used to batch query NFS share client information."""

        url = "nas_protocol/nfs_share_auth_client_list"
        if access_name is not None:
            filter_str = "[{\"share_id\": \"%s\", \"access_name\": \"%s\"}]" % (
                str(extra_param[0]), access_name)
        else:
            filter_str = "[{\"share_id\": \"%s\"}]" % str(extra_param[0])
        filter_para = {
            "filter": filter_str,
            "range": {
                "offset": offset,
                "limit": constants.MAX_QUERY_COUNT
            },
            "account_id": extra_param[1]
        }

        data = jsonutils.dumps(filter_para)
        result = self.call(url, data, "GET")

        if result.get('result', {}).get('code') == 0:
            LOG.info(_("Query NFS share clients success.(nfs_share_id: {0})".format(extra_param[0])))
        else:
            err_msg = _("Query NFS share clients failed.(nfs_share_id: {0})".format(extra_param[0]))
            raise exception.InvalidShare(reason=err_msg)

        return result

    def _get_all_dtree_info_of_namespace(self, offset, extra_param):
        """Get namespace information in batches"""

        url = 'file_service/dtrees'
        query_para = {
            "file_system_id": extra_param[0],
            "range": {"offset": offset,
                      "limit": constants.MAX_QUERY_COUNT}
        }
        data = jsonutils.dumps(query_para)
        result = self.call(url, data, "GET")
        self._assert_result(result, 'Batch query dtree info error.')
        return result
