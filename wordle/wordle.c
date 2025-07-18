//Name: Akshay Kalia
//Date: 04/25/2025
#include <stdio.h>
#define FILEMYS "mystery.txt"
#define maxGuess 6 
#define WORD 6
//Function Prototypes
void getWord(char txtWord[]);
void lowercase(char word[]);
void validity(char letterCount[WORD], int *valid);
void checkCorrect(const char txtWord[WORD], char guesses[maxGuess][WORD], char marker[maxGuess][WORD], int attempts);
void guess(char guesses[][WORD], int attempts);
void game(char guesses[][WORD], char marker[][WORD], int attempts);
int checkWin(char txtWord[WORD], char guesses[][WORD], int attempts);
int main(){
char txtWord[WORD];
char guesses[maxGuess][WORD];
char marker[maxGuess][WORD];
char letterCount[WORD];
int attempts = 0; 

lowercase(txtWord);
getWord(txtWord);
//While loop controlling game: repeats until max guess
while(attempts < maxGuess){
guess(guesses, attempts);
//Check if guess is correct, break if so
if(checkWin(txtWord, guesses, attempts)){
break;
}
//Marks what is right in the word
checkCorrect(txtWord, guesses, marker, attempts); 
game(guesses, marker, attempts);
//Increment attempts used by user
attempts++;
}
//If max number of attempts is reached prompt the user with you lost
if(attempts == maxGuess && checkWin(txtWord, guesses, attempts - 1)==0){
	printf("You lost, better luck next time!\n");
}

return 0;
}
//Function used to get word from File
void getWord(char txtWord[]){
FILE* mys;

mys = fopen(FILEMYS, "r");
	if(mys == NULL){
	printf("Could not open your file\n");
	}
fscanf(mys, "%5s", txtWord);
lowercase(txtWord); 
fclose(mys);
}
//Function used to lowercase word from File
void lowercase(char word[]){
	for(int i = 0; word[i] != '\0'; i++){
	//If letter is upercase convert to lower through ASCII value
	if(word[i] >= 'A' && word[i] <= 'Z'){
	//Use ASCII value to convert to lowercase
	word[i] = word[i] + 32;
	}
	}
	}
//Function checking if user guess is valid no numbers, no words greater or less than 5
void validity(char letterCount[WORD], int *valid){
*valid = 1;
int length = 0;
//If guess is above 5 letters, prompt the user with Your guess is too long
for(length = 0; letterCount[length] != '\0'; length++);
	if(length != WORD - 1){
	printf("Your guess must be 5 letters long.\n");
	//Pointer used to check validity in Main
	*valid = 0;
	}
	else{
	//For checking for guess which is not contained of letters
	for(int i = 0; i < WORD - 1; i++){
	//if ! not 
		if(!((letterCount[i] >= 'a' && letterCount[i] <= 'z') || (letterCount[i] >= 'A' && letterCount[i] <= 'Z'))){
			printf("Your guess must only contain letters.\n");
			*valid = 0; 
			return;
			}
		}
	}
}
//Function using markers for correct letters in wrong place, capitalize if in right place
void checkCorrect(const char txtWord[WORD], char guesses[maxGuess][WORD], char marker[maxGuess][WORD], int attempts){
	int letterChecked [WORD - 1] = {0};
	for(int i = 0; i < WORD - 1; i++){
		if(guesses [attempts][i] == txtWord[i]){
		guesses[attempts][i] = guesses[attempts][i] - 32;
		//Set letter that was already checked = 1 
		letterChecked[i] = 1;
		//We do not need a ^ under a match in the right spot so just leave it blank 
		marker[attempts][i] = '^';
		} 
		else{
		marker[attempts][i] = ' ';
		}
		}
	for(int x = 0; x < WORD - 1; x++){
	//Skip over letters that are already in correct place 
	if(guesses[attempts][x] >= 'A'&& guesses[attempts][x] <= 'Z'){
		continue;
		}
		for(int y = 0; y < WORD - 1; y++){
			if(letterChecked[y] == 0 && guesses[attempts][x] == txtWord[y]){
			marker[attempts][x] = '^';
			letterChecked[y] = 1;
			break;
			}
			}
			}
		}
//Function controlling user input
void guess(char guesses[][WORD], int attempts){
	int valid = 0;
		if(attempts != 5){
		printf("GUESS %d! Enter your guess: ", attempts + 1);
		}
		else{
		printf("FINAL GUESS: ");
		}
		while(valid == 0){
		scanf("%s", guesses[attempts]);
		lowercase(guesses[attempts]);
		validity(guesses[attempts], &valid);
		if(valid == 0){
			printf("Please try again: ");
		}
		}
}
//Function printing the format as well as previous and new guess with markers
void game(char guesses[][WORD], char marker[][WORD], int attempts){
	printf("================================\n");
	for(int i = 0; i <= attempts; i++){
	printf("%s\n", guesses[i]);
	printf("%s\n", marker[i]);
	}
	}
//Function used to check if users guess is == to File word
int checkWin(char txtWord[WORD], char guesses[][WORD], int attempts){
	int lettersMatched = 0;
	for(int i = 0; i < WORD - 1; i++){
	char guessChar = guesses[attempts][i];
		if(guessChar >= 'A' && guessChar <= 'Z'){
			guessChar = guessChar + 32;
		}
		if(txtWord[i] == guessChar){
		lettersMatched++;
		}
		}
	if(lettersMatched == WORD - 1){
	for(int i = 0; i < WORD - 1; i++){
		if(guesses[attempts][i] >= 'a' && guesses[attempts][i] <= 'z'){
		guesses[attempts][i] = guesses[attempts][i] - 32; 
	}
	}
	printf("================================\n");
	printf("                %s           \n", guesses[attempts]);
	if(attempts == 0){
	printf("        You won in %d guess!           \n", attempts + 1);
	printf("                GOATED!           \n");
	}
	else if(attempts == 1 || attempts == 2){
	printf("        You won in %d guesses!           \n", attempts + 1);
	printf("                Amazing!           \n");
	}
	else if(attempts == 3 || attempts == 4){
	printf("        You won in %d guesses!           \n", attempts + 1);
	printf("                Nice!           \n");
	}
	else if(attempts == 5){
	printf("        You won in %d guesses!           \n", attempts + 1);
	}
	return 1;
	}
	return 0;
	}
