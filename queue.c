#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>

typedef struct Node {
    struct Node* next;
    char* data;
} Node;

typedef struct Queue {
    Node* head;
    Node* tail;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
} Queue;

Queue* new_queue(){
    Queue* queue = malloc(sizeof(Queue));
    queue->head = NULL;
    queue->tail = NULL;
    return queue;
}

int push(Queue* queue, char* data) {
    Node* new_node = malloc(sizeof(Node));
    new_node->data = (char*) malloc((strlen(data)+1)*sizeof(char));
    if(new_node == NULL){
        return -1;
    }
    new_node->next = NULL;
    /*new_node->data = data;*/
    strcpy(new_node->data, data);
    pthread_mutex_lock(&queue->mutex);
    if(queue->tail != NULL){
        queue->tail->next = new_node;
    }
    queue->tail = new_node;
    if(queue->head == NULL){
        queue->head = new_node;
    }
    pthread_mutex_unlock(&queue->mutex);
    pthread_cond_signal(&queue->cond);
    return 0;
}


void* pop(Queue* queue) {
    pthread_mutex_lock(&queue->mutex);
    if(queue->head == NULL){
        pthread_mutex_unlock(&queue->mutex);
        return NULL;
    }
    char* data = queue->head->data;
    Node* head;
    while (!(head = queue->head)) {
        pthread_cond_wait(&queue->cond, &queue->mutex);
    }
    if (!(queue->head = head->next)) {
        queue->tail = NULL;
    }
    free(head);
    pthread_mutex_unlock(&queue->mutex);
    return data;
}

void *printname(void *sharedQ)
{
    char* name;
    Queue *q = (Queue *) sharedQ;
    do{
        name = pop(q);
        if (name == NULL)
            pthread_exit(NULL);
        printf("%s\n",name);
    } while(name != NULL);
}

