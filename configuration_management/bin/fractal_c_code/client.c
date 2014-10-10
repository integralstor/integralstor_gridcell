#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h> 
#include<sys/stat.h>
#include<fcntl.h>
#include "fractal.h"

int main(int argc, char *argv[])
{
    int sockfd = 0, n = 0, fd;
    struct sockaddr_in serv_addr; 
    struct cmd	command, response;
    char *filename;
    struct cmd * stpt = &command;
    char sendbuff[1024] , rcvdtxt[2048];
    char buffer[512];
    char *cfgfile;
    int option;
    off_t size;
    char remotecmd[64] = {0, };
    int index;
    struct hostent tcp_host_info;
    struct hostent *hp;
    unsigned long inaddr;

    if(argc < 3)
    {
        printf("Usage: %s <ip of server> <cmd> <filename> \n",argv[0]);
        return 1;
    } 

    if (strcmp (argv[2], "write") ==0)
    {
        option = 4;
	if (argc < 4)
          printf("Usage: %s <ip of server> <cmd> <filename> \n",argv[0]);
        else
	   filename = argv[3];
    }
    else if(strcmp(argv[2], "ping") == 0)
    {
        option = 5;
    }
    else if(strcmp(argv[2], "config") == 0)
    {
       option = 6;
    }
    else if(strcmp(argv[2], "istgt") == 0)
    {
       option = 7;
       if(argc < 4)
       {
          printf(" Usage: %s <ip of server> istgt start/stop/restart \n", argv[0]);
          exit(1);
       }
    }
    else if(strcmp(argv[2], "samba") == 0)
    {
       option = 8;
       if( argc < 4)
       {
          printf("Usage: %s <ip of server> samba start/stop/restart \n", argv[0]);
          exit(1);
       }
    }
    else if(strcmp(argv[2], "nmb") == 0)
    {
       option = 9;
       if( argc < 4)
       {
          printf("Usage: %s <ip of server> nmb start/stop/restart \n", argv[0]);
          exit(1);
       }
    }
    else if(strcmp(argv[2], "winbind") == 0)
    {
       option = 10;
       if( argc < 4)
       {
          printf("Usage: %s <ip of server> winbind start/stop/restart \n", argv[0]);
          exit(1);
       }
    }
    else if(strcmp(argv[2], "get_file") == 0)
    {
       option = 11;
       if(argc < 5)
       {
          printf("Usage: %s <ip of server> get_file <remote_file> <local_file>\n", argv[0] );
          exit(1);
       }
    }
    else if(strcmp(argv[2], "rcmd") == 0)
    {
       option = 12;
       if(argc < 4)
       {
          printf("Usage: %s <ip of server> rcmd <command>\n", argv[0] );
          exit(1);
       }
    }
    //memset(recvBuff, '0',sizeof(recvBuff));
    if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        printf("Error : Could not create socket \n");
        return 1;
    } 

    memset(&serv_addr, '0', sizeof(serv_addr)); 

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT); 

    if ( ( inaddr = inet_addr(argv[1] ) ) != INADDR_NONE )
    {
        bcopy( (char *) &inaddr, (char *) &serv_addr.sin_addr, sizeof(inaddr) );
       tcp_host_info.h_name = NULL;
    }
    else
    {
        if( ( hp = gethostbyname( argv[1] ) ) == NULL)
        {
           printf("Host name error: %s\n", argv[1]);
           exit(1);
        }
        tcp_host_info = *hp;
        bcopy( hp->h_addr, (char *) &serv_addr.sin_addr, hp->h_length);
    } 

/*    if(inet_pton(AF_INET, argv[1], &serv_addr.sin_addr)<=0)
    {
        printf("inet_pton error occured\n");
        return 1;
    } */ 

    if( connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr) ) < 0)
    {
       printf("Error : Connect Failed \n");
       return 1;
    } 
    memset(stpt, 0, sizeof( struct cmd) );

    switch(option)
    {
       case 4:
         stpt->command = WRITE; 
         stpt->offset = 0;
        fd = open(filename, O_RDONLY);
        if(fd == -1)
        {
           printf("File can't be open in read mode\n");
           exit(1);
        }
        size = lseek(fd, 0 , SEEK_END); 
        stpt->size = size; 
        strcpy (stpt->filename, filename);

        memcpy(sendbuff, (char *) stpt, sizeof( struct cmd));
        //memcpy(&sendbuff [sizeof (struct cmd)], data, sizeof(data));
        write(sockfd, sendbuff, sizeof( struct cmd) );

        lseek(fd, 0, SEEK_SET);

        while( n = read(fd, buffer, sizeof(buffer)) )   
        {
           write( sockfd, buffer, n);
           printf("%s \n", buffer);
           buffer[n] = '\0';
        }

        close(fd);
        shutdown(sockfd, 1);

        printf("File is sent \n");

        n = read(sockfd, &response, sizeof(struct cmd)); 
        if (response.command != RESPONSE)
        {
           printf("Response is failure\n");
        } 
        else
        {
           printf("Response is successful\n");
        }
        printf("The response is %d\n", response.command);
        break;

      case 5:
         stpt->command = FRACTAL_PING ; 
         write(sockfd, (char*) stpt, sizeof(struct cmd) );
         n = read(sockfd, &response, sizeof(struct cmd)); 
         if (response.command == PING_RESPONSE)
         {
            printf("Success\n");
         } 
         else
         {
            printf("Failure\n");
         }
         break;

      case 6:
         stpt->command = FRACTAL_CONFIG; 
         write(sockfd, (char*) stpt, sizeof(struct cmd) );
         n = read(sockfd, &response, sizeof(struct cmd) ); 
         if (response.command == CONFIG_RESPONSE)
         {
            printf("Config Response is received\n");
            cfgfile = argv[1];
            strcat(cfgfile, ".status");
            fd = open(cfgfile, O_CREAT | O_WRONLY | O_TRUNC, S_IRWXU);
            if(fd == -1)
            {
               printf("File %s is not created\n", cfgfile);
               exit(1);
            }
            n = read(sockfd, rcvdtxt,1000);
            write(fd, rcvdtxt, n);
            printf("The received config file content is %s\n", rcvdtxt); 
         } 
         else
         {
            printf("Config No Response \n");
         }
         break;

     case 7:
        stpt->command = ISTGT;
        strcpy (stpt->filename, argv[3]);
        write( sockfd, ( char *) stpt, sizeof( struct cmd) );
        n = read(sockfd, &response, sizeof ( struct cmd) );
        if( response.command == SERVICE_RESPONSE )
        {
           printf("Success\n");
        }
        else
        {
           printf("Failure\n");
        }
        break;

      case 8:
        stpt->command = SMB;
        strcpy( stpt->filename, argv[3] );
        write( sockfd, (char *) stpt, sizeof( struct cmd) );
        n = read(sockfd, &response, sizeof( struct cmd) );
        if( response.command == SERVICE_RESPONSE )
        {
           printf("Success\n");
        }
        else
        {
          printf("Failure\n");
        }
        break;

      case 9:
        stpt->command = NMB;
        strcpy( stpt->filename, argv[3] );
        write( sockfd, (char *) stpt, sizeof( struct cmd) );
        n = read(sockfd, &response, sizeof( struct cmd) );
        if( response.command == SERVICE_RESPONSE )
        {
           printf("Success\n");
        }
        else
        {
          printf("Failure\n");
        }
        break;

      case 10:
        stpt->command = WINBIND;
        strcpy( stpt->filename, argv[3] );
        write( sockfd, (char *) stpt, sizeof( struct cmd) );
        n = read(sockfd, &response, sizeof( struct cmd) );
        if( response.command == SERVICE_RESPONSE )
        {
           printf("Success\n");
        }
        else
        {
          printf("Failure\n");
        }
        break;

     case 11:
       stpt->command = GET_FILE;
       strcpy( stpt->filename, argv[3] );
       write( sockfd, (char *) stpt, sizeof( struct cmd) );
       n = read( sockfd, &response, sizeof( struct cmd) );
       if( response.command == GETFILE_RESPONSE )
       {
          printf("Success\n");
          fd = open(argv[4], O_CREAT | O_WRONLY | O_TRUNC, S_IRWXU);
          if(fd == -1)
          {
             printf("File %s is not created\n", argv[4]);
             exit(1);
          }
/*          n = read(sockfd, rcvdtxt,2048);
          write(fd, rcvdtxt, n);
          printf("The received config file content is %s\n", rcvdtxt); 
*/
         write(fd, response.filename, strlen(response.filename) );
       } 
       else
       {
          printf("Config No Response \n");
       }
       break;
 
     case 12:
       strcpy(remotecmd, argv[3]);
       for(index = 4; index < argc; index++)
       {
          strcat(remotecmd, " ");
          strcat(remotecmd, argv[index] );
       }
       strcpy(stpt->filename, remotecmd);
       
       write( sockfd, (char *) stpt, sizeof( struct cmd) );
       n = read(sockfd, &response, sizeof( struct cmd) );
       if( response.command == RCMD_RESPONSE )
       {
          printf("Success\n");
          printf("%s", response.filename);
       }
       else
       {
          printf("Failure\n");
       }
       break;
    
       default:
          printf("It's General Response\n");
    } 
 
    close(sockfd);    
    return 0;
}
