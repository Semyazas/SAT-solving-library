from DIMACS_encoding import DIMACS_decoder


if __name__ == "__main__":
   decoder_nested5 = DIMACS_decoder("tsetin_inputs\\inputs\\nested_5.sat")
   decoder_nested8 = DIMACS_decoder("tsetin_inputs\\inputs\\nested_8.sat")
   decoder_toy5 = DIMACS_decoder("tsetin_inputs\\inputs\\toy_5.sat")

   correct_out1 =[["x1", "x7","not x4"],
        ["x3","x9","x7","x1"],
        ["x3","x4","x9"],
        ["x9","x3","not x6"],
        ['not x3', 'x6', 'x9'],
        ["not x4","not x5","not x6","x3"],
        ["not x4", "not x5", "not x3", "x6"]
   ]
   correct_out2 = [
     ["a1","a2"],
     ["a1","a3"], 
     ["a1","a4"], 
     ["a1","a5"]
   ]

   for decoder, correct_out in zip(
          [decoder_nested5,decoder_toy5],
          [correct_out1,correct_out2]):
     
     decoder.get_var_mapping()
     for found_clause, correct_clause in zip(decoder.clauses,correct_out):
          found_clause.sort()
          correct_clause.sort()

     assert(decoder.clauses == correct_out)
   