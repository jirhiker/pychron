Experiments
-------------

This section describes how to write an experiment with Pychron. A Pychron ``experiment``
in Mass Spec parlance is a ``Multiple Runs Sequence``.

Position Rules
~~~~~~~~~~~~~~~

The following is a list of rules for how a position entry is interpreted

#. 4 or p4 (Goto position 4)
#. 3,4,5 (Goto positions 3,4,5. Treat as one analysis)
#. 7-12 (Goto positions 7,8,9,10,11,12. Treat as individual analyses)
#. 7:12 (Same as #3)
#. 10:16:2 (Goto positions 10,12,14,16. Treat as individual analyses)
#. D1 (Drill position 1)
#. T1-2 (Goto named position T1-2 i.e transect 1, point 2)
#. L3 (Trace path L3)
#. 1-6;9;11;15-20 (Combination of rules 2. and 3. Treat all positions as individual analyses)

Here are a few examples of how Rule #9 is processed

::

    user_input= 1-6;9
    
    #resulting positions
    positions= 1,2,3,4,5,6,9
    
    
    user_input= 1-3;9;11-13
    
    #resulting positions
    positions= 1,2,3,4,5,6,9,11,12,13
    


The starting position, i.e 1 in the above case, can be greater than the end position i.e 6. 
If the start > end, positions will decrease from start to end
::

    user_input= 9;6-1
    
    #resulting positions
    positions= 9,6,5,4,3,2,1
    
    

If auto-increment position is enabled pychron starts incrementing from the last value and follows the same pattern as the rule.

::
    
    user_input= 1-6;9
    
    #resulting auto-incremented positions
    positions= 10-15;18
    
    
    user_input= 1-6
    
    #resulting auto-incremented positions
    positions= 7-12
    

