#currently intended for one specific purpose
#will read in secondary-screen-dose-response-curve-parameters
#and output a new csv that's just the old csv with a new screen_id called 
#HTSwithMTS010_Overlayed that is HTS002 with any duplicates (both depmap_id and name columns the same) from MTS010,
#  overwriting their respective HTS002 values, and adding any MTS010 values that don't exist in HTS002 all added to the end of the file

import pandas as pd
import time  #for seeing how long this takes to run


start_time = time.perf_counter()
#
#read in csv
#
readin_csv = "secondary-screen-dose-response-curve-parameters"
df_csv_import = pd.read_csv(readin_csv + ".csv", index_col=False)

#
#sort csv (to be sorted by screen_id > depmap_id > name)
#
df_sorted_import = df_csv_import.sort_values(by=["name"])
df_sorted_import = df_sorted_import.sort_values(by=["depmap_id"], kind='mergesort')
df_sorted_import = df_sorted_import.sort_values(by=["screen_id"], kind='mergesort')

#time to sort
print("importing and sorting took: ", time.perf_counter() - start_time, " seconds")
start_time = time.perf_counter()

df_sorted_import.to_csv(readin_csv + "_sorted.csv", index = False, na_rep = 'NA')

#
#append or overwrite entries based on comparison
#
study_col = "screen_id"
compare_col_1 = "depmap_id"
compare_col_2 = "name"

#overwriting one study with another
original_screen_id = "HTS002"
overwriting_screen_id = "MTS010"
output_screen_id = "HTSwithMTS010_Overlayed"

original_index = -1
original_end = -1
overwriting_index = -1
overwriting_end = -1
#num_overwritten = 0
#num_appended = 0

#find start and end of both sets of screen_ids (data should already be sorted)
#currently just going to do this by iterating through the whole thing
found_orig_col = False
found_over_col = False

for i in range(len(df_sorted_import)):
    study = df_sorted_import[study_col].iloc[i]
    if study == original_screen_id and found_orig_col == False:
        original_index = i
        found_orig_col = True
    elif study == overwriting_screen_id and found_over_col == False:
        overwriting_index = i
        found_over_col = True
    if found_orig_col == True and study != original_screen_id:
        original_end = i-1
        found_orig_col = False
    elif found_over_col == True and study != overwriting_screen_id:
        overwriting_end = i-1
        found_over_col = False

if original_end == -1:
    original_end = len(df_sorted_import)-1
    #print ("original goes to end of file")
if overwriting_end == -1:
    overwriting_end = len(df_sorted_import)-1
    #print ("overwriting goes to end of file") #expected in this case   
print ("original start: ", original_index, " original end: ", original_end)
print ("overwriting start: ", overwriting_index, " overwriting end: ", overwriting_end)  
  
#time to iterate with for loop    
print("iterating with a for loop took: ", time.perf_counter() - start_time, " seconds")
start_time = time.perf_counter()
#
#actual compare and append/overwrite
#
#I should use a list[of dictionaries?] here and append to the dataframe apparently
#currently may be making a list of series instead of dicts which doesn't seem to be an issue as far as I can tell
#
start_size = original_end - original_index + overwriting_end - overwriting_index +2
overwritten_count = 0
appended_count = 0
excluded_count = 0
list_append = []
try:
    while original_index <= original_end or overwriting_index <= overwriting_end:
        #stop comparing once one is at end
        if overwriting_index > overwriting_end: 
            if isinstance(df_sorted_import[compare_col_1].iloc[original_index], float):
                original_index += 1
                excluded_count += 1
            else:
                list_append.append(df_sorted_import.iloc[original_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                original_index += 1
                appended_count += 1
        elif original_index > original_end:
            if isinstance(df_sorted_import[compare_col_1].iloc[overwriting_index], float):
                overwriting_index += 1
                excluded_count += 1
            else:
                list_append.append(df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                overwriting_index += 1
                appended_count += 1
        #dealing with NA in the depmap_id column
        elif isinstance(df_sorted_import[compare_col_1].iloc[original_index], float): 
            original_index += 1
            excluded_count += 1
        elif isinstance(df_sorted_import[compare_col_1].iloc[overwriting_index], float):
            overwriting_index += 1
            excluded_count += 1
        #normal comparison
        elif df_sorted_import[compare_col_1].iloc[original_index] == df_sorted_import[compare_col_1].iloc[overwriting_index]:
            if df_sorted_import[compare_col_2].iloc[original_index] == df_sorted_import[compare_col_2].iloc[overwriting_index]:
                list_append.append(df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                #print ("overwriting, compound| original index: ", original_index, " overwriting index: ", overwriting_index)
                #print ("appending: ", df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                original_index += 1
                overwriting_index += 1
                overwritten_count += 1
            elif df_sorted_import[compare_col_2].iloc[original_index] < df_sorted_import[compare_col_2].iloc[overwriting_index]:
                list_append.append(df_sorted_import.iloc[original_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                #print ("original, compound| original index: ", original_index, " overwriting index: ", overwriting_index)
                #print ("appending: ", df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                original_index += 1
                appended_count += 1
            elif df_sorted_import[compare_col_2].iloc[original_index] > df_sorted_import[compare_col_2].iloc[overwriting_index]:
                list_append.append(df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                #print ("overwriting, compound| original index: ", original_index, " overwriting index: ", overwriting_index)
                #print ("appending: ", df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
                overwriting_index += 1
                appended_count += 1
        elif df_sorted_import[compare_col_1].iloc[original_index] < df_sorted_import[compare_col_1].iloc[overwriting_index]:
            list_append.append(df_sorted_import.iloc[original_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
            #print ("original, culture| original index: ", original_index, " overwriting index: ", overwriting_index)
            #print ("orig cul: ", df_sorted_import[compare_col_1].iloc[original_index], " over cul: ", df_sorted_import[compare_col_1].iloc[overwriting_index])
            #print("orig drug: ", df_sorted_import[compare_col_2].iloc[original_index], " over drug: ", df_sorted_import[compare_col_2].iloc[overwriting_index])
            #print ("appending: ", df_sorted_import.iloc[original_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
            original_index += 1
            appended_count += 1
        elif df_sorted_import[compare_col_1].iloc[original_index] > df_sorted_import[compare_col_1].iloc[overwriting_index]:
            list_append.append(df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
            #print ("overwriting, culture| original index: ", original_index, " overwriting index: ", overwriting_index)
            #print ("appending: ", df_sorted_import.iloc[overwriting_index].replace([original_screen_id,overwriting_screen_id],output_screen_id))
            overwriting_index += 1
            appended_count += 1
        else:
            print ("this shouldn't happen")
            exit()
        
except KeyError as e:
    cause = e.args[0]
    print ("key error. key: ", cause)

#
#add appended/overwritten study to df
#
        
#output csv
df_sorted_import.to_csv(readin_csv + "_appended.csv", index = False, na_rep = 'NA')
#wait...I can just output the original then output the new in append mode
df_to_append = pd.DataFrame(list_append)
#need to replace study column, plan to replace as I go now
#df_to_append = df_to_append.replace([original_screen_id,overwriting_screen_id],output_screen_id)  
df_to_append.to_csv(readin_csv + "_appended.csv", index = False, header = False, na_rep = 'NA', mode = 'a')
print("time to output: ", time.perf_counter() - start_time, " seconds")
print("original entries: ", start_size)
print("overwritten : ", overwritten_count)
print("appended: ", appended_count)
print("excluded: ", excluded_count)
print("makes sense check: ", overwritten_count*2 + appended_count + excluded_count == start_size)