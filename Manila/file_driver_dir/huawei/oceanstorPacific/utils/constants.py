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

# client config
SOCKET_TIMEOUT = 60

# error code of RE-LOGIN
ERROR_USER_OFFLINE = 1077949069
ERROR_NO_PERMISSION = 1077949058

# error code of TRY AGAIN
ERROR_URL_OPEN = -1
ERROR_SPECIAL_STATUS = (
    33564721,
    33564722,  # tier busy
    33564699,  # filesystem busy
    33656845,  # namespace busy
    37000212,  # internal error
    33561653,
    37120053,  # remote replication busy
    33759517,
    33759518,  # KMS busy
    37000213,  # FSM busy
    37100145,  # FSM remote busy
    50092080,
    33609729,  # reclaiming junk data busy
    31000923,  # delete pool busy
    30400010,  # switch the active node busy
    30160010,  # EDS faulty
    33605891,  # FSA MDC busy
    1073793460,  # system busy
    1077948995,  # memory busy
    1077949006,  # system busy
    1073793332,
    1073793333,  # set busy
    1077949001,  # message busy
    1077949004,  # process busy
    50400004,
    1077949021,  # upgrading
    33623351,  # object name is not exist
    33564736  # file system id is not exist
)

POOL_STATUS_OK = (
    0,  # Normal
    5,  # Migrating data
    7,  # Degraded
    8  # Rebuilding data
)

# error code of NOT EXIST
ACCOUNT_NOT_EXIST = 1800000404
ACCOUNT_ALREADY_EXIST = 1800000409
UNIX_USER_NOT_EXIST = 37749540
UNIX_GROUP_NOT_EXIST = 37749520
NAMESPACE_NOT_EXIST = 33564678
QUOTA_NOT_EXIST = 37767685
QOS_NOT_EXIST = 33623307
TIER_NOT_EXIST = 33564719
POOL_NOT_EXIST = 50120003
NFS_SHARE_NOT_EXIST = 1077939726
CIFS_SHARE_NOT_EXIST = 1077939717
NFS_ACCOUNT_NOT_EXIST = 42514844
REPLICA_PAIR_NOT_EXIST = 37120003
NFS_SHARE_CLIENT_NOT_EXIST = 1077939728
DTREE_NOT_EXIST = 33564767
TIER_POLICY_NOT_EXIST = 33564719
PATH_NOT_EXIST = 33564718

# error code of ALREADY EXIST
NAMESPACE_ALREADY_EXIST = 33656844
QUOTA_ALREADY_EXIST = 37767684
QOS_ALREADY_EXIST = 33623308
TIER_ALREADY_EXIST = 33564716
QOS_ASSOCIATION_ALREADY_EXIST = 33623352
NFS_SHARE_EXIST = 1077939724
NFS_SHARE_CLIENT_EXIST = 1077939727
CIFS_SHARE_CLIENT_EXIST = 1077939718

# namespace config
NOT_FORBIDDEN_DPC = 0
FORBIDDEN_DPC = 1
MULTI_PROTO_SEPARATOR = '_'

#
BASE_VALUE = 1024
POWER_BETWEEN_BYTE_AND_GB = 3
POWER_BETWEEN_KB_AND_GB = 2
POWER_BETWEEN_MB_AND_GB = 1
POWER_BETWEEN_BYTE_AND_MB = 2
DEFAULT_VALID_BITS = 2
CAPACITY_UNIT_KB_TO_GB = 1024 * 1024
CAPACITY_UNIT_BYTE_TO_GB = 1024 * 1024 * 1024
DME_DEFAULT_CAPACITY_UNIT = 'KB'

# quota config
QUOTA_PARENT_TYPE_NAMESPACE = 40
QUOTA_PARENT_TYPE_DTREE = 16445
QUOTA_TYPE_DIRECTORY = 1
QUOTA_UNIT_TYPE_BYTES = 0
QUOTA_UNIT_TYPE_GB = 3
QUOTA_TARGET_NAMESPACE = 1

# qos policy config
QOS_SCALE_NAMESPACE = 0
QOS_MODE_PACKAGE = 2
QOS_PACKAGE_SIZE = 10
MAX_BAND_WIDTH = 30720
BASIC_BAND_WIDTH = 2048
BPS_DENSITY = 250
MAX_IOPS = 3000000
BAND_WIDTH_UPPER_LIMIT = 1073741824
MAX_BPS_DENSITY = 1024000
MAX_IOPS_UPPER_LIMIT = 1073741824000
QOS_UNLIMITED = 0

# Tier policy config
PATH_SEPARATOR = '/'
TIER_GRADE_HOT = '0'
TIER_GRADE_WARM = '1'
TIER_GRADE_COLD = '2'
PERIODIC_MIGRATION_POLICY = 0
ONCE_MIGRATION_POLICY = 1
MATCH_RULE_GT = 3
MATCH_RULE_LT = 2
DTIME_UNIT = 'day'
HTIME_UNIT = 'hour'
MTIME_DEFAULT = 7
MTIME_MAX = 1096
LEN_SQUASH = 2
DICT_ALL_SQUASH = {"all_squash": "0", "no_all_squash": "1"}
DICT_ROOT_SQUASH = {"root_squash": "0", "no_root_squash": "1"}
ATIME_UPDATE_CLOSE = 4294967295
ATIME_UPDATE_HOURS = 3600
GRADE_NAME = '_manila_place'
PERIODICITY_NAME = '_manila_periodicity'
ONCE_MIGRATE_NAME = '_manila_once'
SHARE_PREFIX = "share-"
SORTED_DISK_POOL_TIER_LEVEL = ['4', '0', '1']
DISK_TYPE_SSD = 'ssd'
DISK_TYPE_SAS = 'sas'
DISK_TYPE_SATA = 'sata'
SUPPORT_DISK_TYPES = (DISK_TYPE_SSD, DISK_TYPE_SAS, DISK_TYPE_SATA)
SSD_TOTAL_CAP_KEY = 'ssd_total_capacity_converged'
SAS_TOTAL_CAP_KEY = 'sas_total_capacity_converged'
SATA_TOTAL_CAP_KEY = 'sata_total_capacity_converged'
SSD_USED_CAP_KEY = 'ssd_used_capacity_converged'
SAS_USED_CAP_KEY = 'sas_used_capacity_converged'
SATA_USED_CAP_KEY = 'sata_used_capacity_converged'
TOTAL_CAPACITY_ENUM = {
    DISK_TYPE_SSD: SSD_TOTAL_CAP_KEY,
    DISK_TYPE_SAS: SAS_TOTAL_CAP_KEY,
    DISK_TYPE_SATA: SATA_TOTAL_CAP_KEY
}
USED_CAPACITY_ENUM = {
    DISK_TYPE_SSD: SSD_USED_CAP_KEY,
    DISK_TYPE_SAS: SAS_USED_CAP_KEY,
    DISK_TYPE_SATA: SATA_USED_CAP_KEY
}
DISK_POOL_TIER_ENUM = {
    '0': 'warm',
    '1': 'hot',
    '4': 'cold'
}
TIRE_TASK_PREHEAT = 'Preheat'
TIRE_TASK_PRECOOL = 'Precool'
TIER_MIGRATE_STRATEGY_HOT = 0
TIER_MIGRATE_STRATEGY_COLD = 2
TIER_MIGRATE_DEFAULT_ATIME = 100
TIER_DAY_TO_HOUR = 24

TIER_ENUM = {
    '0': 'hot',
    '1': 'warm',
    '2': 'cold'
}

# Pagination query config
MAX_QUERY_COUNT = 100
DSWARE_SINGLE_ERROR = 2
BYTE_TO_MB = 1024 * 1024
QOS_MODE_MANUAL = 3

# constants
PLUGIN_COMMUNITY_IMPL = "PLUGIN_COMMUNITY_IMPL"
PLUGIN_SUYAN_SINGLE_IMPL = "PLUGIN_SUYAN_SINGLE_IMPL"
PLUGIN_SUYAN_GFS_IMPL = "PLUGIN_SUYAN_GFS_IMPL"
PRODUCT_PACIFIC = 'Pacific'
PRODUCT_PACIFIC_GFS = 'Pacific_GFS'
SUYAN_PRODUCT_IMPL_MAPPING = {
    PRODUCT_PACIFIC: PLUGIN_SUYAN_SINGLE_IMPL,
    PRODUCT_PACIFIC_GFS: PLUGIN_SUYAN_GFS_IMPL
}
VALID_PRODUCTS = [PRODUCT_PACIFIC, PRODUCT_PACIFIC_GFS]

# xml config
STORAGE_REST_URL = "Storage/RestURL"
STORAGE_USER_NAME = "Storage/UserName"
STORAGE_USER_PASSWORD = "Storage/UserPassword"
STORAGE_PRODUCT = "Storage/Product"
STORAGE_RESERVED_PERCENTAGE = "Storage/Reserved_percentage"
STORAGE_MAX_OVER_SUBSCRIPTION_RATIO = "Storage/Max_over_subscription_ratio"
FILESYSTEM_STORAGE_POOL = "Filesystem/StoragePool"

CAP_KB = "KB"
CAP_MB = "MB"
CAP_GB = "GB"
CAP_TB = "TB"
CAP_BYTE = "B"

# DME constants
# DME client config
DME_SOCKET_TIMEOUT = 32
DEFAULT_SEMAPHORE = 10
DME_REQUEST_RETRY_TIMES = 3
DME_RETRY_RELOGIN_CODE = (401,)
DME_HTTP_SUCCESS_CODE = (200, 202)
DME_REST_UPPER_LIMIT_CODE = 429
GFS_CREATE_LOCKED_CODE = 'fileservice.0051'
DME_RETRY_CODE = (DME_REST_UPPER_LIMIT_CODE, GFS_CREATE_LOCKED_CODE)
DME_REST_NORMAL = '0'
DME_LOGIN_URL = "/rest/plat/smapp/v1/sessions"
DME_GFS_MAX_PAGE_COUNT = 1000

# DME OBJCET NOT EXIST ERROR CODE
GFS_NOT_EXIST = ('fileservice.0040',)
GFS_TIER_POLICY_NOT_EXIST = ('fileservice.0061',)
OBJECT_NOT_EXIST = 'common.0005'
GFS_DTREE_NOT_EXIST = (OBJECT_NOT_EXIST, )

# DME OBJECT STATUS
GFS_RUNNING_STATUS_NORMAL = 'normal'

# DME TIER KEY
DME_MIGRATE_PERIODIC = 'periodic'
DME_MIGRATE_ONCE = 'one_off'
DME_ATIME_RATHER_THAN = 'greater_than'

# DME TIER KEY
DME_MIGRATE_PERIODIC = 'periodic'
DME_ATIME_RATHER_THAN = 'greater_than'
