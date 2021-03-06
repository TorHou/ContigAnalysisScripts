#include <fstream>
#include <stdio.h>
#include <stdlib.h>
#include <seqan/align.h>
#include <seqan/graph_msa.h>
#include <seqan/seq_io.h>
#include <seqan/sequence.h>
#include <seqan/basic.h>


using namespace seqan;

int main(int argc, char const ** argv)
{
    if (argc != 4){
        std::cout << "Wrong number of inputs, please provide a path to the infix fasta file and the two contigs." << std::endl;
        std::cout << "$ alignments <infixes.fa> <ctg1.fa> <ctg2.fa>" << std::endl;
        return 1;  // Invalid number of arguments.
    }

    typedef String<Dna> TSequence;                             // sequence type
    typedef StringSet<DnaString> TStringSet;                    // container for strings
    typedef StringSet<TSequence, Dependent<> > TDepStringSet;   // dependent string set
    typedef Graph<Alignment<TDepStringSet> > TAlignGraph;       // alignment graph
    //typedef StringSet<Infix<DnaString>> TInfixSet;

    TSequence ctg1;
    TSequence ctg2;
    CharString id1;
    CharString id2;
    SeqFileIn seqFileIn1(toCString(argv[2]));
    readRecord(id1, ctg1, seqFileIn1);
    SeqFileIn seqFileIn2(toCString(argv[3]));
    readRecord(id2, ctg2, seqFileIn2);

    int len1 = length(ctg1);
    Suffix<DnaString >::Type suf1 = suffix(ctg1,len1-200);
    Prefix<DnaString >::Type pref2 = prefix(ctg2,200);


    //readRecord(id, seq, seqFileIn);
    
    StringSet<CharString> ids;
    Dna5String seq;
    TStringSet all_bridges;

    // Reads all remaining records.
    SeqFileIn seqFileIn(toCString(argv[1]));
    readRecords(ids, all_bridges, seqFileIn);

    //TSequence seq1 = "GTCTTCAAATCCTTCTAGTGAATTTTGAGGTTTTTTTTTT";
    //TSequence seq2 = "TTTTTTTTTTGTGGGTGCTATACTTTCTCTTATATTGCTG";
    
    int nr_of_seqs = length(all_bridges);

    TStringSet sequences;
    TStringSet good_bridges;
    TAlignGraph alignG; 
    int score;
    Align<String<Dna> > infixset;
    //resize(rows(infixset), nr_of_seqs);
    
    for (int i = 0; i < nr_of_seqs; ++i){
        //std::cout << all_bridges[i] << std::endl;
        clear(sequences);
        //appendValue(sequences, ctg1);
        appendValue(sequences, suf1);
        appendValue(sequences, all_bridges[i]);
        clear(alignG);
        alignG = TAlignGraph(sequences);
        score = globalAlignment(alignG, Score<int, Simple>(1, -1, -1), AlignConfig<true, false, true, false>(), LinearGaps());
        //std::cout << "Score: " << score << std::endl;
        //std::cout << alignG << std::endl;
        int tpos = (int) getLastCoveredPosition(alignG,0);
        int nid1 = -1;
        int npos1 = -1;
        getProjectedPosition(alignG,0, tpos-1, nid1, npos1);
        //std::cout << "last covered: " << (int) 0 << "\t" << (int) tpos << std::endl;
        //std::cout << "last covered: " << (int) nid << "\t" << (int) npos << std::endl;
        Suffix<DnaString >::Type suf = suffix(all_bridges[i], npos1+1);
        //std::cout << "Suffix: " << suf << std::endl;

        //std::cout << all_bridges[i] << std::endl;
        clear(sequences);
        appendValue(sequences, pref2);
        appendValue(sequences, all_bridges[i]);
        clear(alignG);
        alignG = TAlignGraph(sequences);
        score = globalAlignment(alignG, Score<int, Simple>(1, -1, -1), AlignConfig<false, true, false, true>(), LinearGaps());
        //std::cout << "Score: " << score << std::endl;
        //std::cout << alignG << std::endl;
        tpos = (int) getFirstCoveredPosition(alignG,0);
        int nid2 = -1;
        int npos2 = -1;
        getProjectedPosition(alignG,0, tpos, nid2, npos2);
        //std::cout << "fist covered: " << (int) 0 << "\t" << (int) tpos << std::endl;
        //std::cout << "first covered: " << (int) nid2 << "\t" << (int) npos2 << std::endl;
        //Prefix<DnaString >::Type pref = prefix(all_bridges[i], npos2+1);
        //std::cout << "Prefix: " << pref << std::endl;
        //std::cout << "npos1: " << npos1 << "   npos2: " << npos2 << std::endl;
        Infix<DnaString >::Type inf;
        if (npos1+1 < npos2){
            inf = infix(all_bridges[i], npos1+1,npos2);
            appendValue(good_bridges, inf);
        }
        //else
         //   inf = infix(all_bridges[i], npos1+1,npos1+1);
        //std::cout << "Infix: " << inf << std::endl;

        //appendValue(infixset, inf);
        //assignSource(row(infixset, i), inf);
    }
    if (length(good_bridges) == 0){
    
        std::cout << "consensus sequence is" << std::endl \
              << "" << "\n";
        exit(0);
    }
    resize(rows(infixset), length(good_bridges));
    for (int i= 0; i < length(good_bridges); ++i){
        assignSource(row(infixset, i), good_bridges[i]);
        
    }
    globalMsaAlignment(infixset, SimpleScore(2,-2,-2,-2));
    std::cout << "Infixe: " << infixset << std::endl;
    String<ProfileChar<Dna> > profile;
    resize(profile, length(row(infixset, 0)));
    for (unsigned rowNo = 0; rowNo < length(good_bridges); ++rowNo)
        for (unsigned i = 0; i < length(row(infixset, rowNo)); ++i)
            profile[i].count[ordValue(getValue(row(infixset, rowNo), i))] += 1;

    // call consensus from this string
    DnaString consensus;
    for (unsigned i = 0; i < length(profile); ++i)
    {
        int idx = getMaxIndex(profile[i]);
        if (idx < 4)  // is not gap
            appendValue(consensus, Dna(getMaxIndex(profile[i])));
    }
    std::cout << "consensus sequence is" << std::endl \
              << consensus << "\n";


    /* this could be a good check
    int score = globalAlignment(alignG1, Score<int, Simple>(1, -1, -1), AlignConfig<true, true, true, true>(), LinearGaps());
    std::cout << "Score: " << score << std::endl;
    std::cout << alignG1 << std::endl;
    */

    /* this doesnt work
    score = globalAlignment(alignG2, Score<int, Simple>(1, -1, -1), AlignConfig<false, true, false, true>(), LinearGaps());
    std::cout << "Score: " << score << std::endl;
    std::cout << alignG2 << std::endl;
    */

    /* this works
    score = globalAlignment(alignG3, Score<int, Simple>(1, -1, -1), AlignConfig<true, false, true, false>(), LinearGaps());
    std::cout << "Score: " << score << std::endl;
    std::cout << alignG3 << std::endl;
    */

    return 0;
}

