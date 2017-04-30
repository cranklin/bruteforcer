typedef struct Queue Queue;

Queue* new_queue();

int push(Queue* queue, char* data);

void* pop(Queue* queue);

