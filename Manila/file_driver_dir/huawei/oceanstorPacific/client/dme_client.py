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

import json

from oslo_log import log

from manila import exception
from manila.i18n import _

from .rest_client import RestClient
from ..utils import constants
from ..utils import driver_utils

LOG = log.getLogger(__name__)


class DMEClient(RestClient):
    """DMEClient class for OceanStorPacific storage system."""

    def __init__(self, driver_config):
        super(DMEClient, self).__init__(driver_config)
        self.base_url = self.driver_config.rest_url
        self.login_url = self.base_url + constants.DME_LOGIN_URL

    @staticmethod
    def _error_code(res):
        """
        get http status code and
        error code from response body if exist
        :param res: response object
        :return: http code
        """
        status_code = res.status_code

        if status_code in constants.DME_HTTP_SUCCESS_CODE:
            return status_code, constants.DME_REST_NORMAL
        result = res.json()
        return status_code, result.get('error_code', constants.DME_REST_NORMAL)

    @staticmethod
    def _assert_result(result, msg_format, special_error_code_param=None):
        """
        Check whether need to raise error or not
        if special error param exist, raise this error
        otherwise, raise common error InvalidRequest
        :param result: url response body
        :param msg_format: common error msg
        :param special_error_code_param: special error dict
        :return: raise error or None
        """

        error_code = result.get('error_code')
        if error_code == constants.DME_REST_NORMAL:
            LOG.debug("DME restful url calling normal")
            return

        if not special_error_code_param:
            msg = (msg_format + 'result: %s.') % result
            LOG.error(msg)
            raise exception.InvalidRequest(msg)

        if error_code in special_error_code_param.get('special_code'):
            error_msg = special_error_code_param.get('error_msg')
            LOG.info(error_msg)
            raise special_error_code_param.get('error_type')(error_msg)

    @staticmethod
    def _check_login_code(result):
        """
        if login failed, get and print the exception reason logs
        :param result: login response result
        :return:
        """
        error_code = result.get('error_code')
        if error_code == constants.DME_REST_NORMAL:
            return

        exception_id = result.get('exceptionId')
        LOG.error('Failed to login DME storage, reason is %s', exception_id)
        raise exception.InvalidRequest(reason=exception_id)

    def retry_relogin(self, old_token):
        """
        Add write lock when do re-login to
        hang up other business restful url
        :param old_token: the old session
        :return:
        """
        with self.call_lock.write_lock():
            self.relogin(old_token)

    def login(self):
        data = {
            "grantType": "password",
            "userName": self.driver_config.user_name,
            "value": self.driver_config.user_password
        }
        self.init_http_head(data, self.login_url)
        # do login
        LOG.info("Begin to login DME storage, the login url is %s", self.login_url)
        res = self._session.put(
            self.login_url, data=json.dumps(data),
            timeout=constants.DME_SOCKET_TIMEOUT,
            verify=self._session.verify
        )
        result = res.json()
        result['error_code'] = self._error_code(res)[1]

        self._check_login_code(result)

        self._session.headers.update({
            "X-Auth-Token": result.get('accessSession')
        })

        self._login_url = self.login_url
        LOG.info("Login the DME Storage success, login_url is %s" % self.login_url)

    def logout(self):
        if not self._login_url:
            return

        try:
            self.semaphore.acquire()
            self._session.delete(self.login_url, timeout=constants.SOCKET_TIMEOUT)
        except Exception as err:
            LOG.warning("Logout DME Client"
                        " failed because of %(reason)s".format(reason=err))
        finally:
            self.semaphore.release()
            self._session.close()
            self._session = None
            self._login_url = None
            LOG.info("Logout the DME Client success, logout_url is %s" % self.login_url)
        return

    def relogin(self, old_token):
        if (self._session and
                self._session.headers.get('X-Auth-Token') != old_token):
            LOG.info('Relogin has been done by other thread, '
                     'no need relogin again.')
            return

        self.logout()
        self.login()

    def query_cluster_statistics_by_name(self, cluster_name):
        url = '/rest/storagemgmt/v1/cluster-classifications/statistics'
        query_param = {
            'name': cluster_name
        }
        result = self.call(url, data=query_param, method='GET')
        self._assert_result(result, "query cluster classifications failed,")
        return result

    def create_gfs(self, gfs_param):
        url = '/rest/fileservice/v1/gfs'
        result = self.call(url, data=gfs_param, method='POST')
        self._assert_result(result, "Create GFS failed,")
        return result

    def create_gfs_dtree(self, gfs_dtree_param):
        url = '/rest/fileservice/v1/gfs/dtrees'
        result = self.call(url, data=gfs_dtree_param, method='POST')
        self._assert_result(result, "Create GFS Dtree failed,")
        return result

    def add_ipaddress_to_gfs(self, gfs_params):
        url = '/rest/fileservice/v1/gfs/dpc-auth-ip-addresses'
        result = self.call(url, data=gfs_params, method='POST')
        self._assert_result(result, "add the ip addresses of the dpc to the gfs failed,")
        return result

    def remove_ipaddress_from_gfs(self, gfs_params):
        url = '/rest/fileservice/v1/gfs/dpc-auth-ip-addresses'
        result = self.call(url, data=gfs_params, method='DELETE')
        self._assert_result(result, "delete the ip addresses of the dpc to the gfs failed,")
        return result

    def change_gfs_size(self, name_locator, new_size_in_gb, new_hot_size):
        url = '/rest/fileservice/v1/gfs'
        new_size_in_kb = driver_utils.convert_capacity(new_size_in_gb, constants.CAP_GB, constants.CAP_KB)
        data = {
            "name_locator": name_locator,
            "quota": {
                "directory_quota": {
                    "space_quota": {
                        "hard_quota": new_size_in_kb,
                        "unit_type": constants.CAP_KB
                    }
                }
            }
        }
        if new_hot_size:
            new_hot_size_in_kb = driver_utils.convert_capacity(new_hot_size, constants.CAP_GB, constants.CAP_KB)
            data["disk_pool_limit"] = {
                "tier_hot_limit": new_hot_size_in_kb,
                "tier_cold_limit": new_size_in_kb - new_hot_size_in_kb,
                "unit_type": constants.CAP_KB
            }
        result = self.call(url, data=data, method='PUT')
        self._assert_result(result, "Change GFS size failed,")
        return result

    def change_gfs_dtree_size(self, name_locator, new_size_in_gb):
        url = '/rest/fileservice/v1/gfs/dtrees/quotas'
        data = {
            "name_locator": name_locator,
            "quota": {
                "directory_quota": {
                    "space_quota": {
                        "hard_quota": new_size_in_gb,
                        "unit_type": constants.CAP_GB
                    }
                }
            }
        }
        result = self.call(url, data=data, method='PUT')
        self._assert_result(result, "Change GFS dtree size failed,")
        return result

    def query_gfs_detail(self, name_locator):
        url = '/rest/fileservice/v1/gfs/detail/query'
        data = {
            "name_locator": name_locator
        }
        result = self.call(url, data=data, method='POST')
        self._assert_result(result, "Query GFS detail failed,")
        return result

    def query_gfs_dtree_detail(self, name_locator):
        url = '/rest/fileservice/v1/gfs/dtrees/detail/query'
        data = {
            "name_locator": name_locator
        }
        result = self.call(url, data=data, method='POST')
        self._assert_result(result, "Query GFS dtree detail failed,")
        return result

    def query_task_by_id(self, task_id):
        url = '/rest/taskmgmt/v1/tasks/{0}'.format(task_id)
        result = self.call(url, None, method='GET')
        self._assert_result(result, "query task {0} failed,".format(task_id))

        # 获取任务信息，任务查询结果是个列表，里面有当前任务及其子任务
        task_list = result.get("data", [])
        root_task = None
        for task in task_list:
            if task.get("id") == task_id:
                root_task = task
                break
        if not root_task:
            msg = (_('query task failed, task not in task list, task id: {0}'.format(task_id)))
            LOG.error(msg)
            raise exception.InvalidShare(msg)

        return root_task

    def wait_task_until_complete(self, task_id, time_out_seconds=60 * 30, query_interval_seconds=3):
        def query_task_callback():
            task_info = self.query_task_by_id(task_id)

            # 任务状态，取值范围：1-初始状态;2-执行中;3-成功;4-部分成功;5-失败;6-超时
            task_status = task_info.get('status')
            if task_status in [1, 2]:
                # 1-初始状态;2-执行中，记录日志，等下个查询间隔
                LOG.info('task {0} status is: {1}, progress: {2}'
                         .format(task_id, task_status, task_info.get('progress')))
                return False
            elif task_status in [4, 5, 6]:
                # 4-部分成功;5-失败;6-超时，抛出异常
                msg = (_('task {0} complete but not success, status is: {1}'.format(task_id, task_status)))
                LOG.error(msg)
                raise exception.InvalidShare(reason=msg)
            elif task_status == 3:
                # 3-成功，反True
                return True
            else:
                # 其他情况，抛异常
                msg = (_('task {0} unknown status, status is: {1}'.format(task_id, task_status)))
                LOG.error(msg)
                raise exception.InvalidShare(reason=msg)

        driver_utils.wait_for_condition(query_task_callback, query_interval_seconds, time_out_seconds)

    def delete_gfs(self, gfs_delete_param):
        url = '/rest/fileservice/v1/gfs/delete'
        result = self.call(url, data=gfs_delete_param, method='POST')
        not_found_error_param = {
            'special_code': constants.GFS_NOT_EXIST,
            'error_msg': 'Delete gfs failed because of gfs not exist',
            'error_type': exception.ShareNotFound
        }
        self._assert_result(result, "Delete GFS failed,",
                            special_error_code_param=not_found_error_param)
        return result

    def delete_gfs_dtree(self, gfs_dtree_delete_param):
        url = '/rest/fileservice/v1/gfs/dtrees/delete'
        result = self.call(url, data=gfs_dtree_delete_param, method='POST')
        not_found_error_param = {
            'special_code': constants.GFS_DTREE_NOT_EXIST,
            'error_msg': 'Delete gfs dtree failed because of gfs or dtree not exist',
            'error_type': exception.ShareNotFound
        }
        self._assert_result(result, "Delete GFS Dtree failed,",
                            special_error_code_param=not_found_error_param)
        return result

    def get_gfs_info_by_name(self, gfs_query_param):
        url = '/rest/fileservice/v1/gfs/query'
        result = self.call(url, data=gfs_query_param, method='POST')
        self._assert_result(result, 'Query GFS info failed,')
        return result.get('data', [])