import subprocess


class TestVirtV2V:
    def test_build_command(self, virt_v2v_instance):
        vcenter_username = virt_v2v_instance.params["vcenter_username"]
        vcenter_hostname = virt_v2v_instance.params["vcenter_hostname"]
        esxi_hostname = virt_v2v_instance.params["esxi_hostname"]
        vddk_libdir = virt_v2v_instance.params["vddk_libdir"]
        vddk_thumbprint = virt_v2v_instance.params["vddk_thumbprint"]
        conversion_host_id = virt_v2v_instance.params["conversion_host_id"]
        vm_name = virt_v2v_instance.params["vm_name"]
        expected_cmd = [
            "virt-v2v",
            "-ip",
            "/tmp/passwd",
            "-ic",
            f"esx://{vcenter_username}@{vcenter_hostname}/Datacenter/{esxi_hostname}?no_verify=1",
            "-it",
            "vddk",
            "-io",
            f"vddk-libdir={vddk_libdir}",
            "-io",
            f"vddk-thumbprint={vddk_thumbprint}",
            "-o",
            "openstack",
            "-oo",
            f"server-id={conversion_host_id}",
            vm_name,
        ]
        assert virt_v2v_instance.build_command() == expected_cmd

    def test_run_command_success(self, mocker, virt_v2v_instance):
        mocker.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=["virt-v2v"], returncode=0, stdout="output", stderr=""
            ),
        )
        cmd = virt_v2v_instance.build_command()
        result = virt_v2v_instance.run_command(cmd)
        assert result["changed"] is True
        assert result["stdout"] == "output"

    def test_run_command_failure(self, mocker, virt_v2v_instance):
        mocker.patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(
                returncode=1, cmd="virt-v2v", output="error_output", stderr="error"
            ),
        )
        cmd = virt_v2v_instance.build_command()
        result = virt_v2v_instance.run_command(cmd)
        assert result["changed"] is False
        assert (
            result["msg"]
            == "Command failed: Command 'virt-v2v' returned non-zero exit status 1."
        )
        assert result["stdout"] == "error_output"
        assert result["stderr"] == "error"
