//Binary search Tree algorithm
#include <stdio.h>

struct ptree_t 
{
	int v;
	struct ptree_t* left;
	struct ptree_t* right;
	struct ptree_t* parent;
};

void visit(struct ptree_t* t)
{
	return;
}

//traverse a binary tree with parent pointer
//O(1) auxillary space
void inorder_traverseO1(struct ptree_t* root)
{
	struct ptree_t* curr = root;
	struct ptree_t* next = NULL;
	struct ptree_t* last_visit = NULL;
	while (curr != NULL) {
		if (last_visit == curr->right) {
			next = curr->parent;	
		} else if (last_visit == curr->left) {
			visit(curr);
			if (curr->right != NULL) {
				next = curr->right;
			} else {
				next = curr->parent;
			}
		} else {
			if (curr->left != NULL) {
				next = curr->left;
			} else {
				visit(curr);	
				if (curr->right != NULL) {
					next = curr->right;
				} else {
					next = curr->parent;
				}
			}
		}
		last_visit = curr;
		curr = next;
	}
}

int main()
{
	return 0;
}
