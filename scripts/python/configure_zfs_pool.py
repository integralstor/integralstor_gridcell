
import sys
import os
import re
from integralstor_utils import zfs


def configure_zfs_pool():
    pool_created = False
    try:
        os.system('clear')

        print 'Scanning for disks..'
        free_disks, err = zfs.get_free_disks()
        if err:
            raise Exception(err)
        print 'Scanning for disks.. Done.'
        print

        if not free_disks or len(free_disks) < 2:
            raise Exception(
                'There are insufficient unused disks available to create a pool')

        pool_types = []
        num_free_disks = len(free_disks)

        if num_free_disks == 2:
            pool_types.append(('mirror', 'Mirror'))
            default = 'mirror'
            default_str = 'Mirror'
        if num_free_disks >= 3:
            pool_types.append(('raid5', 'RAID-5'))
            default = 'raid5'
            default_str = 'RAID-5'
        if num_free_disks >= 4:
            default = 'raid5'
            default_str = 'RAID-5'
            pool_types.append(('raid6', 'RAID-6'))
            if num_free_disks / 2 == 0:
                # Allow this only for even numbered free disks
                pool_types.append(('raid10', 'RAID-10'))

        print 'The following underlying ZFS pool disk storage configuration types are possible : '
        print

        i = 1
        for pool_type in pool_types:
            print '%d. %s ' % (i, pool_type[1])
            i += 1

        print
        print

        str_to_print = 'Select a ZFS pool type (1-%d) (Default is %s, Press enter to select to default) : ' % (
            len(pool_types), default_str)
        valid_input = False
        pool_num = -1
        while not valid_input:
            input = raw_input(str_to_print)
            if input:
                try:
                    pool_num = int(input)
                    if pool_num > 0 and pool_num <= (len(pool_types) + 1):
                        valid_input = True
                        selected_pool_type = pool_types[(pool_num - 1)][0]
                except Exception, e:
                    pass
            else:
                selected_pool_type = default
                valid_input = True
            if not valid_input:
                print "Invalid value. Please try again."
        print

        # print selected_pool_type

        print 'Determining disks to be used for ZFS pool creation..'
        vdev_list = None
        if selected_pool_type in ['raid5', 'raid6']:
            vdev_list, err = zfs.create_pool_data_vdev_list(
                selected_pool_type, num_raid_disks=num_free_disks)
        elif cd['selected_pool_type'] == 'raid10':
            vdev_list, err = zfs.create_pool_data_vdev_list(
                selected_pool_type, stripe_width=num_free_disks / 2)
        else:
            vdev_list, err = zfs.create_pool_data_vdev_list(selected_pool_type)
        if err:
            raise Exception(err)
        print 'Determining disks to be used for pool creation.. Done.'
        print
        # print 'vdevlist', vdev_list

        print 'Creating ZFS pool..'
        result, err = zfs.create_pool(
            'frzpool', selected_pool_type, vdev_list, dedup=False)
        if not result:
            if not err:
                raise Exception('Unknown error!')
            else:
                raise Exception(err)
        pool_created = True
        print 'Creating ZFS pool.. Done.'
        print

        '''
    quota_str = None
    pd, err = zfs.get_pool('frzpool')
    if err:
      raise Exception(err)
    val_str = pd['properties']['available']['value']
    ret = re.match('([0-9.]+)([A-Za-z]*)', val_str)
    #print ret.groups()
    components = ret.groups()
    if ret and components:
      val = float(ret.groups()[0])
      #print val
      if len(components) > 1:
        quota_str = '%.2f%s'%(val*0.85, components[1])
      else:
        quota_str = '%.2f'%(val*0.85)
    #print 'quota str', quota_str
    '''

        print 'Creating ZFS filesystems..'
        ret, err = zfs.create_dataset('frzpool', 'normal', None)
        # print 'create normal', ret, err
        if err:
            raise Exception(err)
        ret, err = zfs.create_dataset(
            'frzpool', 'deduplicated', {'dedup': 'on'})
        # print 'create dedup', ret, err
        if err:
            raise Exception(err)
        ret, err = zfs.create_dataset(
            'frzpool', 'compressed', {'compression': 'on'})
        # print 'create compr', ret, err
        if err:
            raise Exception(err)
        ret, err = zfs.create_dataset('frzpool', 'local_storage', None)
        if err:
            raise Exception(err)
        os.system('chmod 775 /frzpool/local_storage')
        print 'Creating ZFS filesystems.. Done.'
        print

        '''
    print 'Setting ZFS pool quota..'
    if quota_str:
      ret, err = zfs.update_property('frzpool', 'quota', quota_str)
      #print 'setting pool quota ', ret, err
      if err:
        raise Exception(err)
      ret, err = zfs.update_property('frzpool/normal', 'quota', quota_str)
      #print 'setting normal quota ', ret, err
      if err:
        raise Exception(err)
      ret, err = zfs.update_property('frzpool/deduplicated', 'quota', quota_str)
      #print 'setting dedup quota ', ret, err
      if err:
        raise Exception(err)
      ret, err = zfs.update_property('frzpool/compressed', 'quota', quota_str)
      if err:
        raise Exception(err)
      #print 'setting compressed quota ', ret, err
    print 'Setting ZFS pool quota.. Done.'
    print
    '''

        print 'Setting ZFS pool properties..'
        ret, err = zfs.update_property('frzpool', 'acltype', 'posixacl')
        # print 'setting acltype', ret, err
        if err:
            raise Exception(err)
        ret, err = zfs.update_property('frzpool', 'xattr', 'sa')
        # print 'setting xattr', ret, err
        if err:
            raise Exception(err)
        ret, err = zfs.update_property('frzpool', 'atime', 'off')
        # print 'setting atime', ret, err
        if err:
            raise Exception(err)
        print 'Setting ZFS pool properties.. Done.'
        print

    except Exception, e:
        if pool_created:
            print 'Error occurred so destroying ZFS pool'
            ret, err = zfs.delete_pool('frzpool')
            if err:
                print 'Error destroying pool : %s' % err
        return -1, 'Error configuring ZFS pools : %s' % str(e)
    else:
        return 0, None


if __name__ == '__main__':

    rc, err = configure_zfs_pool()
    if err:
        print err
    sys.exit(rc)

# vim: tabstop=8 softtabstop=0 expandtab ai shiftwidth=4 smarttab
