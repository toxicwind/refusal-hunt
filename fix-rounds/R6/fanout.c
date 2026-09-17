/* fanout: precompiled parallel command orchestrator.
   usage: fanout <timeout_s> <cmd1> [cmd2 ...] — each cmd via sh -c, concurrent.
   prints "leg=i rc=N ms=M cmd=..." per leg; exit 0 iff all legs rc==0. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/wait.h>
static long long ms_now(void){
  struct timeval tv; gettimeofday(&tv,0);
  return (long long)tv.tv_sec*1000LL + tv.tv_usec/1000;
}
int main(int argc, char** argv){
  if(argc < 4){ fprintf(stderr,"usage: fanout <timeout_s> <cmd1> [cmd2 ...]\n"); return 2; }
  int n = argc - 2;
  long long timeout_ms = atoll(argv[1]) * 1000LL;
  pid_t* pids = calloc(n, sizeof(pid_t));
  long long* t0 = calloc(n, sizeof(long long));
  int* rc = malloc(n * sizeof(int));
  long long* dt = malloc(n * sizeof(long long));
  for(int i=0;i<n;i++){ rc[i]=-99; dt[i]=-1; }
  long long start = ms_now();
  for(int i=0;i<n;i++){
    t0[i] = ms_now();
    pid_t p = fork();
    if(p==0){ execl("/bin/sh","sh","-c",argv[2+i],(char*)0); _exit(127); }
    if(p<0){ rc[i]=126; dt[i]=0; } else pids[i]=p;
  }
  int left = n;
  for(int i=0;i<n;i++) if(rc[i]!=-99) left--;
  while(left > 0){
    long long now = ms_now();
    int timed_out = (now - start > timeout_ms);
    if(timed_out) for(int i=0;i<n;i++) if(rc[i]==-99 && pids[i]>0) kill(pids[i], SIGKILL);
    for(int i=0;i<n;i++){
      if(rc[i]!=-99 || pids[i]<=0) continue;
      int st; pid_t w = waitpid(pids[i], &st, WNOHANG);
      if(w==pids[i]){ rc[i]=WIFEXITED(st)?WEXITSTATUS(st):128; dt[i]=ms_now()-t0[i]; left--; }
      else if(w==-1 && errno==ECHILD){ rc[i]=125; dt[i]=ms_now()-t0[i]; left--; }
    }
    if(left>0) usleep(5000);
    if(ms_now() - start > timeout_ms + 8000) break;
  }
  int bad=0;
  for(int i=0;i<n;i++){
    if(rc[i]==-99){ rc[i]=124; dt[i]=ms_now()-t0[i]; }
    if(rc[i]!=0) bad++;
    printf("leg=%d rc=%d ms=%lld cmd=%.60s\n", i, rc[i], dt[i], argv[2+i]);
  }
  fflush(stdout);
  free(pids); free(t0); free(rc); free(dt);
  return bad?1:0;
}
