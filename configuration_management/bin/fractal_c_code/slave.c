#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include<sys/stat.h>
#include<fcntl.h>
#include<stdlib.h>
#include <time.h> 
#include "fractal.h"

int main(int argc, char *argv[])
{
    int listenfd = 0, connfd = 0;
    struct sockaddr_in serv_addr; 

    int n, fd;
    char buff[100], sendbuff[2048];
    char txtbuff[2048];
    struct cmd req, resp;
    struct cmd * stpt, *newstpt;
    stpt = & req;
    newstpt = &resp;
    FILE *fp;
    int count = 0;
    char ser_cmd[32] = "service";
    FILE * pf; 
    char path[64];

    if( (listenfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        printf("Error: Couldn't creta socket\n");
        exit(1);
    }
    memset(&serv_addr, '0', sizeof(serv_addr));
    memset(sendbuff, '0', sizeof(sendbuff)); 

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    serv_addr.sin_port = htons(PORT); 

    if( bind(listenfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) == -1)
    {
       printf("Error: Couldn't bind address\n");
       exit(1);
    } 

    if( listen(listenfd, 10) == -1)  
    {
       printf("Error: Couldn't listen\n");
       exit(1);
    }
    while(1)
    {
        memset(newstpt, 0, sizeof(struct cmd) );  
        if( (connfd = accept(listenfd, (struct sockaddr*)NULL, NULL)) == -1)
        {
           printf("Error: accept system call failed\n");
           exit(1);
        }
        if( read(connfd, sendbuff, sizeof(struct cmd) ) == -1)
        {
           printf("Read system call failed\n");
           exit(1);
        }
        memcpy(stpt, sendbuff, sizeof( struct cmd));
#ifdef DEBUG
         printf("The file name is %s\n",stpt->filename);
         printf("The command is %d\n", stpt->command);
         printf("The offset is %d\n", stpt->offset);
         printf("The size to be write is %d\n", stpt->size);
#endif
        if( stpt->command == WRITE)
        {
           if( access(stpt->filename, R_OK | W_OK) != -1)
           {
              fd = open(stpt->filename, O_WRONLY);
           }
           else
           {
              fd = open(stpt->filename, O_CREAT | O_WRONLY);
           } 
           if(fd == -1)
           {
              printf("File creation failed %s\n", strerror(errno) );
              exit(1);
           }
           fchmod(fd, S_IRUSR| S_IWUSR | S_IRGRP | S_IWGRP);

           count = 0;
           while(count < stpt->size)  
           {
              n = read ( connfd, sendbuff, stpt->size - count) ;
             sendbuff[n] = '\0';
             write(fd,sendbuff,n);
             count += n;  
           }
           printf("File received and value of count is %d \n", count);
           close(fd);
           if(stpt->size != count)
           {
             printf("It dint write all the bytes\n");
             newstpt -> command = NORESPONSE;
           }
           else
           {
              newstpt -> command = RESPONSE;
           }
           printf("The value of  command is %d",newstpt->command);
           memcpy(buff, newstpt, sizeof( struct cmd));
           write(connfd, buff, sizeof( struct cmd));
        }
	else if ( stpt->command == FRACTAL_PING)
	{	/* Send ping reponse */
	    newstpt->command = PING_RESPONSE;
	    write(connfd, (char *) newstpt,sizeof(struct cmd) );
	}
	else if (stpt->command == FRACTAL_CONFIG)
	{
		// Open /config/self.cfg file
		// read the file using read (1000 bytes)\
		// prepare the header with response 
		// send response structure
		// send read buffer
		fd = open("/config/self.status", O_RDONLY);
                if(fd == -1)
                { 
                   //printf("File not exist\n");
			fd = open("/config/previous/self.status", O_RDONLY);	
			if(fd == -1)
			{
				printf("File not exist \n");
				exit(1);
			}
			//exit(1);
                }
		n = read(fd,txtbuff, 1000); 
	        newstpt->command = CONFIG_RESPONSE;
	        newstpt	-> size = n;
		write(connfd, (char*) newstpt, sizeof(struct cmd) );
		write(connfd, txtbuff,n);
	}
        else if( stpt->command == ISTGT )
        {
           strcat(ser_cmd, " istgt ");
           strcat(ser_cmd, stpt->filename); 
           if( system(ser_cmd) == -1)
           {
              printf("service command unsuccessful\n");
              newstpt->command = NORESPONSE;
           }
           else
           { 
              newstpt->command = SERVICE_RESPONSE;
           }
           write(connfd, (char *)newstpt, sizeof ( struct cmd) );
        }
        else if( stpt->command == SMB )
        {
           strcat(ser_cmd, " smb ");
           strcat(ser_cmd, stpt->filename );
           if( system(ser_cmd) == -1)
           {
              printf("service command unsuccessful\n");
              newstpt->command = NORESPONSE;
           }
           else
           {
              newstpt->command = SERVICE_RESPONSE;
           }
           write(connfd, (char *)newstpt, sizeof ( struct cmd ) );
        } 
        else if( stpt->command == NMB )
        {
           strcat(ser_cmd, " nmb ");
           strcat(ser_cmd, stpt->filename );
           printf("%s\n", ser_cmd);
           if( system(ser_cmd) == -1)
           {
              printf("service command unsuccessful\n");
              newstpt->command = NORESPONSE;
           }
           else
           {
              newstpt->command = SERVICE_RESPONSE;
           }
           write(connfd, (char *)newstpt, sizeof ( struct cmd ) );
        } 
        else if( stpt->command == WINBIND )
        {
           strcat(ser_cmd, "  winbind ");
           strcat(ser_cmd, stpt->filename );
#if 0
           pf = popen(ser_cmd, "r");
           if( pf == NULL)
           {
              printf("Remote command unsuccessful\n");
              newstpt->command = NORESPONSE;
           }
           else
           {
              fgets(path, 64, pf);
              strcpy(newstpt->filename, path);
              while(fgets(path, 64, pf) !=NULL )
                strcat(newstpt->filename, path);  
              newstpt->command = SERVICE_RESPONSE;
              printf("%s", newstpt->filename);
           }
#endif
#if 1
           if( system(ser_cmd) == -1)
           {
              printf("service command unsuccessful\n");
              newstpt->command = NORESPONSE;
           }
           else
           {
              newstpt->command = SERVICE_RESPONSE;
           }
#endif
           write(connfd, (char *)newstpt, sizeof ( struct cmd ) );
//           pclose(pf);
        } 
	else if (stpt->command == GET_FILE)
	{
		fp = fopen(stpt->filename, "r");
                if(fp == NULL)
                { 
			printf("File not exist \n");
                        newstpt->command = NORESPONSE;
		}
                else
                {
                   memset(path, 0, 64);
                   fgets(path, 64, fp);
                   strcpy(newstpt->filename, path);
                   while(fgets(path, 64, fp) != NULL )
                      strcat(newstpt->filename, path);  
                   newstpt->command = GETFILE_RESPONSE;
                   //printf("%s", newstpt->filename);
                }
	        write(connfd, (char*) newstpt, sizeof(struct cmd) );
	}
        else
        {
          pf = popen(stpt->filename, "r");
          if( pf == NULL)
          {
              printf("Remote command unsuccessful\n");
              newstpt->command = NORESPONSE;
          }
          else
          {
              memset(path, 0, 64);
              fgets(path, 64, pf);
              strcpy(newstpt->filename, path);
              while(fgets(path, 64, pf) !=NULL )
                strcat(newstpt->filename, path);  
              if( pclose(pf) != 0)
                 newstpt->command = NORESPONSE;
              else
                 newstpt->command = RCMD_RESPONSE;
              //printf("%s", newstpt->filename);
          }
              
          write(connfd, (char *)newstpt, sizeof ( struct cmd ) );
       }
      close(connfd);
     }
     close(listenfd);
     sleep(1);
}

