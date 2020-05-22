## Cloud-based Personal File Storage
#### Implement a Python program that provides Cloud-based Personal File Storage using Amazon S3.
The personal file storage client program will support following operations:
1. create a directory
2. upload file to a directory. Overwrite destination file if it already exists. Save file extension as Metadata or tags when uploading the file object to S3
3. download file from a directory. If a source file with the name already exists in the current folder, create its
backup by renaming it.
4. delete file from a directory
5. delete directory
6. search files with specific extension. If Directory Name is specified, search for files within that directory (bucket). If Directory Name is not specified, search for files within all directories (buckets). You can search files (objects) by comparing the object's extension saved as part
of Object's Metadata.
7. list directories (buckets) / list files (objects) within a directory (bucket)
You will use S3 as the backend storage for your program.
