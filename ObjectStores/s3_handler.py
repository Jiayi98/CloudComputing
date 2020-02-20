import ast
import boto3
import logging
import os
import sys
import time
import traceback

from botocore.exceptions import ClientError

LOG_FILE_NAME = 'output.log'

REGION = 'us-west-2'

class S3Handler:
    """S3 handler."""

    def __init__(self):
        self.client = boto3.client('s3')

        logging.basicConfig(filename=LOG_FILE_NAME,
                            level=logging.DEBUG, filemode='w',
                            format='%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger("S3Handler")

    def help(self):
        print("Supported Commands:")
        print("1. createdir <bucket_name>")
        print("2. upload <source_file_name> <bucket_name> [<dest_object_name>]")
        print("3. download <dest_object_name> <bucket_name> [<source_file_name>]")
        print("4. delete <dest_object_name> <bucket_name>")
        print("5. deletedir <bucket_name>")
        print("6. find <file_extension> [<bucket_name>] -- e.g.: 1. find txt  2. find txt bucket1 --")
        print("7. listdir [<bucket_name>]")
    
    def _error_messages(self, issue):
        error_message_dict = {}
        error_message_dict['incorrect_parameter_number'] = 'Incorrect number of parameters provided'
        error_message_dict['not_implemented'] = 'Functionality not implemented yet!'
        error_message_dict['bucket_name_exists'] = 'Directory already exists.'
        error_message_dict['bucket_name_empty'] = 'Directory name cannot be empty.'
        error_message_dict['missing_source_file'] = 'Source file cannot be found.'
        error_message_dict['non_existent_bucket'] = 'Directory does not exist.'
        error_message_dict['non_existent_object'] = 'Destination Object does not exist.'
        error_message_dict['unknown_error'] = 'Something was not correct with the request. Try again.'
        error_message_dict['operation_not_permitted'] = 'Not authorized to access resource.'
        error_message_dict['non_empty_bucket'] = 'Directory is not empty.'

        if issue:
            return error_message_dict[issue]
        else:
            return error_message_dict['unknown_error']

    def _get_file_extension(self, file_name):
        # print('得到extension：{}'.format(os.path.exists(file_name)))
        if os.path.exists(file_name):
            # print('得到extension：.splitext={}'.format(os.path.splitext(file_name)))
            return os.path.splitext(file_name)

    def _get(self, bucket_name):
        response = ''
        try:
            response = self.client.head_bucket(Bucket=bucket_name)
        except Exception as e:
            # print(e)
            # traceback.print_exc(file=sys.stdout)
            
            response_code = e.response['Error']['Code']
            if response_code == '404':
                return False
            elif response_code == '403':
                # print('403 错误')
                return self._error_messages('operation_not_permitted')
            elif response_code == '200':
                return True
            else:
                raise e
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False

    def createdir(self, bucket_name):
        if not bucket_name:
            return self._error_messages('bucket_name_empty')

        try:
            return_val = self._get(bucket_name)
            if type(return_val) == str:
                # 403 error
                return return_val
            if return_val:
                return self._error_messages('bucket_name_exists')

            self.client.create_bucket(Bucket=bucket_name,
                                      CreateBucketConfiguration={'LocationConstraint': REGION})
        except Exception as e:
            print(e)
            raise e

        # Success response
        operation_successful = ('Directory %s created.' % bucket_name)
        return operation_successful

    def listdir(self, bucket_name):

        if bucket_name:
            # 检查是否有bucket_name，print('IN LISTDIR : {}'.format(bucket_name))
            # If bucket_name is provided, check that bucket exits.
            try:
                return_val = self._get(bucket_name)
                if not return_val:
                    return self._error_messages('non_existent_bucket')
                if type(return_val) == str:
                    # '403' Error
                    return return_val
            except Exception as e:
                print(e)
                raise e

            # If bucket_name is provided then display the names of all objects in the bucket
            response = self.client.list_objects_v2(Bucket=bucket_name)
            # a list of dict containing Metadata about each object returned
            # print(response)
            # 处理'KeyCount': 0
            if response['KeyCount'] > 0:
                contents_list = response['Contents']
                res = []
                for d in contents_list:
                    res.append(d['Key'])
                # Success response
                res_string = ','.join(res)
                operation_successful = res_string
                return operation_successful
            else:
                return ''
        else:
            # If bucket_name is empty then display the names of all the buckets
            # Returns a list of all buckets
            buckets_list = self.client.list_buckets()['Buckets']
            res = []
            for d in buckets_list:
                res.append(d['Name'])

            # Success response
            res_string = ','.join(res)
            operation_successful = res_string
            return operation_successful

    def upload(self, source_file_name, bucket_name, dest_object_name=''):
        print('检查所有参数{}-{}-{}'.format(source_file_name,bucket_name,dest_object_name))

        # 1. Parameter Validation
        #    - source_file_name exits in current directory
        #    - bucket_name exists
        if not os.path.exists(source_file_name):
            print('找不到这个文件')
            self._error_messages('missing_source_file')
        print('本地存在{}'.format(source_file_name))
        try:
            # check if bucket_name exists
            return_val = self._get(bucket_name)
            if not return_val:
                return self._error_messages('non_existent_bucket')
            if type(return_val) == str:
                # '403' Error
                return return_val
        except Exception as e:
            print(e)
            raise e


        # 3. SDK call
        #    - When uploading the source_file_name and add it to object's meta-data
        #    - Use self._get_file_extension() method to get the extension of the file.
        try:
            extension = self._get_file_extension(source_file_name)[1][1:]
            # print('Extension是{}'.format(extension))
            self.client.upload_file(
                source_file_name,
                bucket_name,
                dest_object_name,
                ExtraArgs={'Metadata':{'extension':extension}}
            )
        # except Exception as e: #
        except ClientError as e:
            # print('上传文件出错',e)
            return self._error_messages('unknown_error')

        # Success response
        operation_successful = ('File %s uploaded to bucket %s.' % (source_file_name, bucket_name))
        return operation_successful

    def download(self, dest_object_name, bucket_name, source_file_name=''):
        # if source_file_name is not specified then use the dest_object_name as the source_file_name
        # print('检查参数: {}/{}/[{}]'.format(dest_object_name, bucket_name,source_file_name))
        # If the current directory already contains a file with source_file_name then move it as a backup
        # with following format: <source_file_name.bak.current_time_stamp_in_millis>
        if os.path.exists(source_file_name):

            milli_sec = int(round(time.time() * 1000))
            new_name = '{}.bak.{}'.format(source_file_name,milli_sec)
            # print('本地存在同名文件,改名为：{}'.format(new_name))
            os.rename(source_file_name, new_name)
        # Parameter Validation
        try:
            # check if bucket_name exists
            return_val = self._get(bucket_name)
            if not return_val:
                return self._error_messages('non_existent_bucket')
            if type(return_val) == str:
                # '403' Error
                return return_val
        except Exception as e:
            print(e)
            raise e

        try:
            self.client.get_object(Bucket=bucket_name, Key=dest_object_name)
        except Exception as e:
            # print('文件不存在: {}'.format(dest_object_name))
            # print('文件不存在: {}'.format(e))
            return self._error_messages('non_existent_object')

        # SDK Call
        self.client.download_file(bucket_name, dest_object_name, source_file_name)
        # Success response
        operation_successful = ('Object %s downloaded from bucket %s.' % (dest_object_name, bucket_name))
        return operation_successful


    def delete(self, dest_object_name, bucket_name):
        # Parameter Validation
        # print('检查参数: {}-{}'.format(dest_object_name,bucket_name))
        try:
            # check if bucket_name exists
            return_val = self._get(bucket_name)
            if not return_val:
                return self._error_messages('non_existent_bucket')
            if type(return_val) == str:
                # '403' Error
                return return_val
        except Exception as e:
            print(e)
            raise e

        try:
            self.client.get_object(Bucket=bucket_name, Key=dest_object_name)
        except Exception as e:
            # print('文件不存在: {}'.format(dest_object_name))
            # print('文件不存在: {}'.format(e))
            return self._error_messages('non_existent_object')

        response = self.client.delete_object(
            Bucket=bucket_name,
            Key=dest_object_name
        )
        # Success response
        operation_successful = ('Object %s deleted from bucket %s.' % (dest_object_name, bucket_name))
        return operation_successful


    def deletedir(self, bucket_name):
        # Parameter Validation
        try:
            # check if bucket_name exists
            return_val = self._get(bucket_name)
            if not return_val:
                return self._error_messages('non_existent_bucket')
            if type(return_val) == str:
                # '403' Error
                return return_val
        except Exception as e:
            print(e)
            raise e

        # Delete the bucket only if it is empty
        response = self.client.list_objects_v2(Bucket=bucket_name)
        # a list of dict containing Metadata about each object returned
        if response['KeyCount'] > 0:
            return self._error_messages('non_empty_bucket')
        else:
            response = self.client.delete_bucket(Bucket=bucket_name)
            # Success response
            operation_successful = ("Deleted bucket %s." % bucket_name)
            return operation_successful



    def find(self, file_extension, bucket_name=''):
        # print('检查参数：{}-[{}]'.format(file_extension,bucket_name))
        # Return object names that match the given file extension
        if not bucket_name:
        # If bucket_name is empty then search all buckets
            # print('没有指定bucket')
            response = self.client.list_buckets()
            res_file_list = []
            # Output the bucket names
            # print('存在以下buckets:')
            for bucket in response['Buckets']:
                # print(bucket['Name'])
                file_list_str = self.find(file_extension,bucket['Name'])
                if len(file_list_str) > 0:
                    res_file_list.append(file_list_str)
            return ','.join(res_file_list)

        else:
        # If bucket_name is specified then search for objects in that bucket.
            response = self.client.list_objects_v2(Bucket=bucket_name)
            if response['KeyCount'] > 0:
                contents_list = response['Contents']
                res = []
                for d in contents_list:
                    file_name = d['Key']
                    # print('文件名={}'.format(file_name))
                    response_obj = self.client.get_object(Bucket=bucket_name,Key=file_name)
                    # print(response_obj)
                    if response_obj['Metadata']:
                        if response_obj['Metadata']['extension'] == file_extension:
                            # print('找到一个：{}'.format(file_name))
                            res.append(file_name)
                return ','.join(res)
            else:
                return ''


    def dispatch(self, command_string):
        parts = command_string.split(" ")
        response = ''

        if parts[0] == 'createdir':
            # Figure out bucket_name from command_string
            if len(parts) > 1:
                bucket_name = parts[1]
                response = self.createdir(bucket_name)
            else:
                # Parameter Validation
                # - Bucket name is not empty
                response = self._error_messages('bucket_name_empty')
        elif parts[0] == 'upload':
            # Figure out parameters from command_string
            # source_file_name and bucket_name are compulsory; dest_object_name is optional
            # Use self._error_messages['incorrect_parameter_number'] if number of parameters is less
            # than number of compulsory parameters
            if len(parts) == 4:
                source_file_name = parts[1]
                bucket_name = parts[2]
                dest_object_name = parts[3]
            elif len(parts) == 3:
                source_file_name = parts[1]
                bucket_name = parts[2]
                dest_object_name = source_file_name
            else:
                return self._error_messages('incorrect_parameter_number')
            response = self.upload(source_file_name, bucket_name, dest_object_name)
        elif parts[0] == 'download':
            # Figure out parameters from command_string
            # dest_object_name and bucket_name are compulsory; source_file_name is optional
            # Use self._error_messages['incorrect_parameter_number'] if number of parameters is less
            # than number of compulsory parameters
            if len(parts) == 4:
                source_file_name = parts[3]
                bucket_name = parts[2]
                dest_object_name = parts[1]
            elif len(parts) == 3:
                bucket_name = parts[2]
                dest_object_name = parts[1]
                source_file_name = dest_object_name
            else:
                return self._error_messages('incorrect_parameter_number')
            response = self.download(dest_object_name, bucket_name, source_file_name)
        elif parts[0] == 'delete':
            if len(parts) == 3:
                dest_object_name = parts[1]
                bucket_name = parts[2]
                response = self.delete(dest_object_name, bucket_name)
            else:
                return self._error_messages('incorrect_parameter_number')
        elif parts[0] == 'deletedir':
            if len(parts) == 2:
                bucket_name = parts[1]
                response = self.deletedir(bucket_name)
            else:
                return self._error_messages('incorrect_parameter_number')
        elif parts[0] == 'find':
            if len(parts) == 3:
                file_extension = parts[1]
                bucket_name = parts[2]
            elif len(parts) == 2:
                file_extension = parts[1]
                bucket_name = ''
            else:
                return self._error_messages('incorrect_parameter_number')
            response = self.find(file_extension, bucket_name)
        elif parts[0] == 'listdir':
            bucket_name = ''
            if len(parts) > 1:
                bucket_name = parts[1]
            response = self.listdir(bucket_name)
        else:
            response = "Command not recognized."
        return response


def main():

    s3_handler = S3Handler()
    
    while True:
        try:
            command_string = ''
            if sys.version_info[0] < 3:
                command_string = raw_input("Enter command ('help' to see all commands, 'exit' to quit)>")
            else:
                command_string = input("Enter command ('help' to see all commands, 'exit' to quit)>")
    
            # Remove multiple whitespaces, if they exist
            command_string = " ".join(command_string.split())
            
            if command_string == 'exit':
                print("Good bye!")
                exit()
            elif command_string == 'help':
                s3_handler.help()
            else:
                response = s3_handler.dispatch(command_string)
                print(response)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()