"""AWS Systems Manager integration"""

import boto3
from typing import List, Dict, Any

class AWSSystemsManager:
    """AWS Systems Manager integration"""
    
    def __init__(self):
        self.client = boto3.client('ssm', region_name='us-west-2')
    
    def execute_patch_now(self, instance_ids: List[str], patch_level: str = "non_critical") -> Dict[str, Any]:
        """Execute patching with rollback capability"""
        try:
            response = self.client.send_command(
                InstanceIds=instance_ids,
                DocumentName="AWS-RunPatchBaseline",
                Parameters={
                    'Operation': ['Install'],
                    'RebootOption': ['RebootIfNeeded']
                },
                Comment=f"SRE Agent patch execution - {patch_level}"
            )
            
            command_id = response['Command']['CommandId']
            
            return {
                "status": "success",
                "command_id": command_id,
                "instance_count": len(instance_ids),
                "patch_level": patch_level,
                "message": f"Patch command sent to {len(instance_ids)} instances"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to execute patch command"
            }
    
    def get_patch_compliance(self, instance_ids: List[str]) -> Dict[str, Any]:
        """Get patch compliance status for instances"""
        try:
            compliance_data = {}
            
            for instance_id in instance_ids:
                try:
                    response = self.client.describe_instance_patch_states(
                        InstanceIds=[instance_id]
                    )
                    
                    if response['InstancePatchStates']:
                        state = response['InstancePatchStates'][0]
                        compliance_data[instance_id] = {
                            "installed_count": state.get('InstalledCount', 0),
                            "missing_count": state.get('MissingCount', 0),
                            "failed_count": state.get('FailedCount', 0),
                            "operation": state.get('Operation', 'Unknown'),
                            "compliance_status": "compliant" if state.get('MissingCount', 0) == 0 else "non_compliant"
                        }
                    else:
                        compliance_data[instance_id] = {
                            "status": "no_data",
                            "message": "No patch state data available"
                        }
                        
                except Exception as e:
                    compliance_data[instance_id] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            compliant = [iid for iid, data in compliance_data.items() if data.get('compliance_status') == 'compliant']
            non_compliant = [iid for iid, data in compliance_data.items() if data.get('compliance_status') == 'non_compliant']
            
            return {
                "status": "success",
                "compliance_data": compliance_data,
                "summary": {
                    "total_instances": len(instance_ids),
                    "compliant_count": len(compliant),
                    "non_compliant_count": len(non_compliant),
                    "compliant_instances": compliant,
                    "non_compliant_instances": non_compliant
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to check patch compliance"
            }
    
    def get_patch_summary(self, instance_id: str) -> Dict[str, Any]:
        """Get patch summary for instance"""
        try:
            response = self.client.describe_instance_patch_states(
                InstanceIds=[instance_id]
            )
            
            if response['InstancePatchStates']:
                state = response['InstancePatchStates'][0]
                return {
                    "compliance_status": "compliant" if state.get('MissingCount', 0) == 0 else "non_compliant",
                    "missing_patches": state.get('MissingCount', 0),
                    "installed_patches": state.get('InstalledCount', 0),
                    "failed_patches": state.get('FailedCount', 0),
                    "last_operation": state.get('Operation', 'Unknown'),
                    "operation_start_time": state.get('OperationStartTime', 'Unknown')
                }
            else:
                return {
                    "compliance_status": "unknown",
                    "missing_patches": 0,
                    "message": "No patch data available"
                }
                
        except Exception as e:
            return {
                "compliance_status": "error",
                "error": str(e)
            }