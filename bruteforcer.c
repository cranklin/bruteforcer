/*
gcc -c queue.c
gcc -pthread -std=c99 queue.c bruteforcer.c
*/
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include "queue.h"

#define MAX_THREADS 30
#define MAX_COMMAND_LENGTH 100
#define COMMAND_BUFFER 1024
#define CHARSET_BUFFER 95
#define MAX_WORD_LENGTH 20
static const char COMMAND_SUFFIX[] = " > /dev/null 2>&1";

typedef struct Config {
	int numThreads;
	int statusCode;
	int length;
	char *marker;
	int lowerAlphabet;
	int upperAlphabet;
	int numbers;
	int symbols;
	int verbose;
	char *dictionaryFile;
	char *command;
} Config;

typedef struct ThreadConfig {
    int statusCode;
    int verbose;
	int length;
    char *marker;
    char *command;
    char *charset;
    Queue *queue;
} ThreadConfig;

pthread_t tid[MAX_THREADS];
int *ret_val[MAX_THREADS];
volatile int exit_flag = 0;
char charset[CHARSET_BUFFER];

void* processAttempt(void *arg)
{
    ThreadConfig *threadConfig = arg;
	char* word;
    char* marker;
    char command[COMMAND_BUFFER];
    int retCode = 0;
    pthread_t id = pthread_self();
    /* pointer to the first occurrence of the marker */
    marker = strstr(threadConfig->command, threadConfig->marker);
    /* pointer to marker - pointer to beginning of command string = length in bytes to copy */
    memcpy(command, threadConfig->command, marker - threadConfig->command);
    do{
        word = pop(threadConfig->queue);
        if (word == NULL)
            pthread_exit(NULL);
        /* destination is pointer to the start of command + length of bytes to start of marker */
        memcpy(command + (marker - threadConfig->command), word, strlen(word));
        /* copy the rest of the command string */
        memcpy(command + ((marker - threadConfig->command) + strlen(word)), marker + strlen(threadConfig->marker), strlen(marker - strlen(threadConfig->marker)) + 1);
        memcpy(command + (strlen(threadConfig->command) + strlen(word) - 2), COMMAND_SUFFIX, strlen(COMMAND_SUFFIX)+1);
        /*printf("%s @ %p - %lu\n",word, (void*)&word, id);*/
        /*printf("%s - %lu\n",word, id);*/
        retCode = system(command);
        /*printf("%s - %lu\n", command, id);*/
        if (retCode == threadConfig->statusCode){
            exit_flag = 2;
            printf("\n\n***** PASSWORD FOUND *****\npassword: %s\n***** PASSWORD FOUND *****\n\n\n", word);
        }
        free(word);
    } while(word != NULL && exit_flag == 0);

    pthread_exit((void*)0);
}

void* generateWords(void *arg)
{
    ThreadConfig *threadConfig = arg;
    int base = strlen(threadConfig->charset);
    printf("Charset(%d): %s\n", base, threadConfig->charset);

    unsigned long long int j, quotient, dividend, numWords = 1;
    for (int i = 0; i < threadConfig->length; i++){
        /* calculating the base 10 length of our password list */
        numWords *= base;
    }
    printf("Number of possible words: %llu\n", numWords);

    int wordIndices[MAX_WORD_LENGTH];
    for (j = 0; j < numWords; j++){
        if (exit_flag > 0)
            break;
        /* this is where all the password generating magic happens
         * let's convert our base conversion math from base 10 to
         * base charset and retrieve the characters by its index */
        int counter = -1;
        dividend = j;
        do{
            counter++;
            quotient = dividend / base;
            wordIndices[counter] = dividend % base;
            dividend = quotient;
            /*printf("%d,", wordIndices[counter]);*/
        } while(dividend > 0);

        /* wordIndices holds the index of each character little end.
         * let's reverse and map
         */
        char word[MAX_WORD_LENGTH];
        for (int i = 0; i <= counter; i++){
            word[i] = threadConfig->charset[wordIndices[counter-i]];
            /*printf("%d: %c\n", i, word[i]);*/
        }
        word[counter+1] = '\0';
        /*printf("Current word(%d): %s @ %p\n", counter, word, (void *)&word);*/
        push(threadConfig->queue, word);
    }
}

char* generateCharset(Config config)
{
    /* repeating the first element of each charset is a hack to work around the imperfections of the base method being used */
    char *lowerAlphabetCharset = "aabcdefghijklmnopqrstuvwxyz";
    char *upperAlphabetCharset = "AABCDEFGHIJKLMNOPQRSTUVWXYZ";
    char *numbersCharset = "00123456789";
    char *symbolsCharset = "~~`!@#$%^&*()-_=+\\|[]{},.<>/?;:'\"";

    charset[0] = '\0';
    if(config.lowerAlphabet == 1){
        strcat(charset, lowerAlphabetCharset);
    }
    if(config.upperAlphabet == 1){
        strcat(charset, upperAlphabetCharset);
    }
    if(config.numbers == 1){
        strcat(charset, numbersCharset);
    }
    if(config.symbols == 1){
        strcat(charset, symbolsCharset);
    }
    return charset;
}

void printConfig(Config config)
{
    printf("Lowercase alphabet: %d\n", config.lowerAlphabet);
    printf("Uppercase alphabet: %d\n", config.upperAlphabet);
    printf("Numbers: %d\n", config.numbers);
    printf("Symbols: %d\n", config.symbols);
    printf("Dictionary file: %s\n", config.dictionaryFile);
    printf("Number of threads: %d\n", config.numThreads);
    printf("Desired status code: %d\n", config.statusCode);
    printf("Length: %d\n", config.length);
    printf("Marker: %s\n", config.marker);
    printf("Command to brute force: %s\n", config.command);
}

int main(int argc, char *argv[])
{
	Config config = {1, 0, 8, "{}", 0, 0, 0, 0, 0, "", ""};
    ThreadConfig *threadConfig = malloc(sizeof(ThreadConfig));
    Queue* q = new_queue();

    int i = 0;

	if(argc < 2){
		return 1;
	}
	else{
		for (i = 1; i < argc; i++){
			if (!strcmp(argv[i], "-h")){
				return 0;
			}
			else if (!strcmp(argv[i], "-v")){
				return 0;
			}
			else if (!strcmp(argv[i], "-a")){
				config.lowerAlphabet = 1;
			}
			else if (!strcmp(argv[i], "-A")){
				config.upperAlphabet = 1;
			}
			else if (!strcmp(argv[i], "-N")){
				config.numbers = 1;
			}
			else if (!strcmp(argv[i], "-S")){
				config.symbols = 1;
			}
			else if (!strcmp(argv[i], "-V")){
				config.verbose = 1;
			}
			else if (!strcmp(argv[i], "-d")){
				i++;
				config.dictionaryFile = argv[i];
			}
			else if (!strcmp(argv[i], "-n")){
				i++;
				config.numThreads = atoi(argv[i]);
			}
			else if (!strcmp(argv[i], "-s")){
				i++;
				config.statusCode = atoi(argv[i]);
			}
			else if (!strcmp(argv[i], "-l")){
				i++;
				config.length = atoi(argv[i]);
			}
			else if (!strcmp(argv[i], "-m")){
				i++;
				config.marker = argv[i];
			}
			else{
                char cmd[MAX_COMMAND_LENGTH] = "";
                while(i < argc){
                    strcat(cmd, argv[i]);
                    strcat(cmd, " ");
                    i++;
                }
                config.command = &cmd[0];
			}
		}
	}

    int err;
    printConfig(config);
    threadConfig->statusCode = config.statusCode;
    threadConfig->verbose = config.verbose;
    threadConfig->marker = config.marker;
    threadConfig->command = config.command;
    threadConfig->length = config.length;
    threadConfig->charset = generateCharset(config);
    threadConfig->queue = q;
    printf("Desired status code: %d\n", threadConfig->statusCode);
    printf("Command to brute force: %s\n", threadConfig->command);

    for(int i = 0; i < config.numThreads + 1; i++){
        if (i == 0){
            err = pthread_create(&(tid[i]), NULL, &generateWords, (void *)threadConfig);
            printf("Starting word generation thread...\n");
            /*sleep(5);*/
        }
        else{
            err = pthread_create(&(tid[i]), NULL, &processAttempt, (void *)threadConfig);
        }
        if (err != 0){
            printf("\ncan't create thread :[%s]", strerror(err));
        }
        else{
            printf("\n Thread %d created successfully\n", i);
        }
    }

    for(int i = 0; i < config.numThreads + 1; i++){
        pthread_join(tid[i], (void**)&(ret_val[i]));
    }

    free(threadConfig);

    return 0;
}
