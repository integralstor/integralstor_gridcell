#define PORT 5005

#define	OPEN	1
#define	CLOSE	2
#define	READ	3
#define	WRITE	4
#define	FRACTAL_PING	5
#define	FRACTAL_CONFIG	6
#define ISTGT      7
#define SMB        8
#define NMB        9
#define WINBIND    10
#define GET_FILE   11

#define	RESPONSE	100
#define PING_RESPONSE   101
#define CONFIG_RESPONSE 102
#define NORESPONSE      103
#define SERVICE_RESPONSE 104
#define GETFILE_RESPONSE 105
#define RCMD_RESPONSE    106

struct	cmd
{
	int	command;
	char	filename[2048];
	int	offset;
	int	size;
};

/* read (sd, buffer, size)

size max will be : sizeof (struct cmd) + 1000; */


