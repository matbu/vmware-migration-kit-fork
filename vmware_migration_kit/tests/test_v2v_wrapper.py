import pytest
import subprocess

from ansible_collections.os_migrate.vmware_migration_kit.plugins.module_utils.v2v_wrapper import VirtV2V


@pytest.fixture()
def virt_v2v_instance():
    params = {
        'vcenter_username': 'test_user',
        'vcenter_hostname': 'test_host',
        'esxi_hostname': 'test_esxi',
        'vddk_libdir': '/usr/lib/vmware-vix-disklib',
        'vddk_thumbprint': 'XX:XX:XX:XX',
        'conversion_host_id': 'test_conversion_id',
        'vm_name': 'test_vm'
    }
    return VirtV2V(params)

class TestVirtV2V:
    def test_build_command(self, virt_v2v_instance):
        expected_cmd = [
            'virt-v2v',
            '-ip', '/tmp/passwd',
            '-ic', f"esx://{virt_v2v_instance.params['vcenter_username']}@{virt_v2v_instance.params['vcenter_hostname']}/Datacenter/{virt_v2v_instance.params['esxi_hostname']}?no_verify=1",
            '-it', 'vddk',
            '-io', f"vddk-libdir={virt_v2v_instance.params['vddk_libdir']}",
            '-io', f"vddk-thumbprint={virt_v2v_instance.params['vddk_thumbprint']}",
            '-o', 'openstack',
            '-oo', f"server-id={virt_v2v_instance.params['conversion_host_id']}",
            virt_v2v_instance.params['vm_name']
        ]
        assert virt_v2v_instance.build_command() == expected_cmd

    def test_run_command_success(self, mocker, virt_v2v_instance):
        mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(args=['virt-v2v'], returncode=0, stdout='output', stderr=''))
        cmd = virt_v2v_instance.build_command()
        result = virt_v2v_instance.run_command(cmd)
        assert result['changed'] is True
        assert result['stdout'] == 'output'
        assert result['stderr'] == ''

    def test_run_command_failure(self, mocker, virt_v2v_instance):
        mocker.patch('subprocess.run', side_effect=subprocess.CalledProcessError(returncode=1, cmd='virt-v2v', output='error_output', stderr='error'))
        cmd = virt_v2v_instance.build_command()
        result = virt_v2v_instance.run_command(cmd)
        assert result['changed'] is False
        assert result['msg'] == 'Command failed: Command failed: 1'
        assert result['stdout'] == 'error_output'
        assert result['stderr'] == 'error'
