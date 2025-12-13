/*
  - read in a cleartext notebook and encode it

  Parameters:
    - (clear text) input notebook
    - output file name for encoded notebook

  g++ -std=c++20 -o encode encode.cpp base64.cpp && ./encode 01.ipynb 01

  2023 Johannes Lange
*/


#include "base64.h"

#include <fstream>
#include <iostream>
#include <iterator>
#include <unistd.h>

int main(int argc, char *argv[])
{

   if (argc != 3) {
      std::cerr << "Error: Two arguments expected: input file name, output file name" << "\n";
      return 1;
   }
   std::string ifname(argv[1]);
   std::string ofname(argv[2]);

   std::ifstream nb_file(ifname);
   std::string nb_content(std::istreambuf_iterator<char>{nb_file}, {});
   nb_file.close();

   nb_content = base64_encode(nb_content);

   std::ofstream out_file(ofname);
   out_file << nb_content;
   out_file.close();
}
