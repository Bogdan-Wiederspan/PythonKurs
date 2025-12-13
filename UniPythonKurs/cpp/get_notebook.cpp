/*
    - read in an encoded notebook
    - decode it
    - replace DUMMYUSER in metadata with the username

    g++ -std=c++20 -o get_notebook get_notebook.cpp base64.cpp && ./get_notebook && ./get_notebook 04

    2023 Johannes Lange
    2024 Marcel Rieger (simple additions)
*/


#include "base64.h"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>

#include <pwd.h>
#include <unistd.h>


std::string DEPLOYMENT_DIR = "/afs/physnet.uni-hamburg.de/users/ex_ba/mrieger/public/.python-ss24-semester-deployment/";

bool replaceSubstring(std::string& str, const std::string& ssold, const std::string& ssnew)
{
    size_t start_pos = str.find(ssold);
    if (start_pos == std::string::npos) return false;
    str.replace(start_pos, ssold.length(), ssnew);
    return true;
}

bool contains(const std::string& str, const std::string& substr)
{
    return str.find(substr) != std::string::npos;
}

bool endsWith(const std::string& stack, const std::string& needle) {
    if (needle.empty()) {
        return false;
    }
    return stack.find(needle, stack.size() - needle.size()) != std::string::npos;
}

int main(int argc, char *argv[])
{
    if (argc > 2) {
        std::cerr << "Error: One argument expected: input file name" << "\n";
        return 1;
    }
    // map: short filename (= 2-digit number) -> full filename; e.g. 23 -> 23_super_important_topic
    std::map<std::string, std::string> notebook_names;
    for (const auto& entry: std::filesystem::directory_iterator(DEPLOYMENT_DIR)) {
        std::string const filename(entry.path().filename());
        // filename has the format 00_topic or 00_exercise_topic, extract everything up to topic
        size_t ex_pos = filename.find("_exercise");
        std::string const shortname = filename.substr(0, ex_pos == std::string::npos ? filename.find("_") : ex_pos + 9);
        notebook_names[shortname] = filename;
    }
    if (argc == 1) {
        std::cout << "Available notebooks:" << "\n";
        for (const auto& notebook_name: notebook_names) {
            // short name
            std::cout << notebook_name.first << std::endl;
        }
        return 0;
    }

    std::string shortname(argv[1]);  // argument corresponds to short name
    if (notebook_names.find(shortname) == notebook_names.end()) {
        std::cout << "File " << shortname << " does not exist. Check available files using " << argv[0] << "\n";
        return 1;
    }
    std::string ifname(notebook_names[shortname]);
    assert(std::filesystem::exists(DEPLOYMENT_DIR + ifname));

    std::ifstream nb_file(DEPLOYMENT_DIR + ifname);
    std::string nb_content(std::istreambuf_iterator<char>{nb_file}, {});
    nb_file.close();

    if (endsWith(nb_content, "\n")) nb_content.pop_back();

    nb_content = base64_decode(nb_content);
    assert(contains(nb_content, "DUMMYUSER"));
    std::string username(getpwuid(getuid())->pw_name);
    replaceSubstring(nb_content, "DUMMYUSER", username);

    std::string ofname(ifname + ".ipynb");
    std::ofstream out_file(ofname);
    out_file << nb_content;
    out_file.close();

    std::cout << "Fetched notebook " << ofname << "\n";

    return 0;
}
