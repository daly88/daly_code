#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <set>
#include <vector>

//shuffle an int array
void shuffle_fisher_yates(std::vector<int> &arr)
{
	int i = arr.size(), j;
	int tmp;
	if ( i == 0 ) return;
	while ( --i ) {
		j = rand() % (i + 1);
		tmp = arr[i];
		arr[i] = arr[j];
		arr[j] = tmp;
	}
}

// input: integer m, n , m < n
// output:  m unique random sorted number in 0 ~ n-1
// time: O(n) Space: O(1)
// by Knuth
void pick_m_knuth(int m, int n, std::vector<int> &output)
{
	int t = m;
	int p = 0;
	int i;
	if (m > n) return;
	output.clear();
	output.reserve(m);
	for(i=0; i<n; i++) {
		if (rand() % (n - i) < t) {
			printf("%d ", i);
			output.push_back(i);
			++p;
			--t;
		}
	}
}

//Purpose: pick a single, random combination of values. sampling algorithm
//time: O(mlogm), space: O(m)
//by Robert Floyd
//proof: http://math.stackexchange.com/questions/178690/whats-the-proof-of-correctness-for-robert-floyds-algorithm-for-selecting-a-sin
void pick_m_floyd(int m, int n, std::vector<int> &output)
{
	int i, j;
	std::set<int> res;
	output.clear();
	output.reserve(m);
	
	for(i=n-m; i<n; i++) {
		j = rand() % i;
		if (res.find(j) == res.end()) {
			res.insert(j);
			output.push_back(j);
		} else {
			res.insert(i);
			output.push_back(i);
		}
	}
}

int main()
{
	std::vector<int> buf;
	srand(time(NULL));
	//pick_m_knuth(4, 8, buf);
	pick_m_floyd(4, 100, buf);
	for(int i=0; i<buf.size(); i++) {
		printf("%d ", buf[i]);
	}
	printf("\n");
	return 0;
}
