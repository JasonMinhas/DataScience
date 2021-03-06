import pandas as pd
import numpy as np
import re
import seaborn as sns
import matplotlib.pyplot as plt

dete_df = pd.read_csv('http://opendata.dete.qld.gov.au/human-resources/dete-exit-survey-january-2014.csv', encoding='cp1252')
dete_df['source'] = 'Department of Education, Training and Employment'
tafe_df = pd.read_csv('http://opendata.dete.qld.gov.au/human-resources/tafe-employee-exit-survey-access-database-december-2013.csv', encoding='cp1252')
tafe_df['source'] = 'Technical and Further Education'

# transpose and get list of responses for each column
def df_column_summary(df):

    summary_dict = {}
    df.apply(
        lambda ser: summary_dict.update({ser.name: list(ser.unique())}))
    df_preview = pd.Series(summary_dict).reset_index().rename(columns={'index': 'column_names', 0: 'list_of_values'})

    return df_preview

dete_preview = df_column_summary(dete_df)
tafe_preview = df_column_summary(tafe_df)

# print to excel file so you can map the headers
dete_preview['dataset_origin'] = 'Department of Education, Training and Employment'
tafe_preview['dataset_origin'] = 'Technical and Further Education'
merged_preview_unclean = pd.concat([dete_preview, tafe_preview], axis='index')
# save to excel file
# merged_preview_unclean.to_excel('C:/Users/jason/personal_projects/DataScience/Clean And Analyze Employee Exit Surveys/header_summary/exit_survey_header_summary.xlsx', index=False)

# --------dete cleaning-------------
# function to remove month so that it matches tafe_df naming convention
def get_year(element):

    if bool(re.match(r'[0-9]{2}/[0-9]{4}', element)):
        return re.findall(r'[0-9]{2}/([0-9]{4})', element)[0]
    return element

# apply get_year() function
dete_df['Cease Date'] = dete_df['Cease Date'].apply(get_year)

# convert date columns to numeric
date_col = ['Cease Date', 'DETE Start Date', 'Role Start Date']
dete_df[date_col] = dete_df[date_col].replace('Not Stated', np.nan)
dete_df[date_col] = dete_df[date_col].apply(pd.to_numeric)

# get length of service
dete_df['LengthofServiceOverall'] = dete_df['Cease Date'] - dete_df['DETE Start Date']
dete_df['LengthofServiceCurrent'] = dete_df['Cease Date'] - dete_df['Role Start Date']

# categorize service length to match
labels = ['Less than 1 year', '1-2', '3-4', '5-6', '7-10', '11-20', 'More than 20 years']
bins = [0, .99999, 2, 4, 6, 10, 20, np.inf]
dete_df['LengthofServiceOverall'] = pd.cut(dete_df['LengthofServiceCurrent'], bins=bins, labels=labels)
dete_df['LengthofServiceCurrent'] = pd.cut(dete_df['LengthofServiceCurrent'], bins=bins, labels=labels)

# replace likert columns with full name to match tafe_df
likert_col = ['My say', 'Career Aspirations', 'Worklife balance', 'Stress and pressure support',
              'Performance of supervisor', 'Information', 'Peer support', 'Feedback', 'Further PD',
              'Professional Development', 'Opportunities for promotion', 'Wellness programs', 'Kept informed',
              'Communication', 'Physical environment', 'Health & Safety', 'Coach', 'Initiative',
              'Skills', 'Workplace issue', 'Staff morale']


likert_dict = {
    'SA': 'Strongly Agree',
    'A': 'Agree',
    'N': 'Neutral',
    'D': 'Disagree',
    'SD': 'Strongly Disagree',
    'M': 'M'
}

dete_df[likert_col] = dete_df[likert_col].apply(lambda ser: ser.map(likert_dict))

# replace results of '56-60' and '61 or older' with '56 or older'

age_repl_dict = {
    '56-60': '56 or older',
    '61 or older': '56 or older'
}

dete_df['Age'] = dete_df['Age'].replace(age_repl_dict)

# --------tafe cleaning-------------

# clean all boolean columns
contributing_cols = [col for col in tafe_df.columns if 'Contributing Factors. ' in col]
before = tafe_df[contributing_cols]
tafe_df[contributing_cols] = tafe_df[contributing_cols].apply(
    lambda ser: ser.map({ser.name.replace('Contributing Factors. ', ''): True})
)
# convert contributing_cols to bool by filling nan with False
tafe_df[contributing_cols] = tafe_df[contributing_cols].fillna(False)

# combine 'Contributing Factors. Study' and 'Contributing Factors. Travel' to match dete_df
study_travel_col = ['Contributing Factors. Study', 'Contributing Factors. Travel']
tafe_df['Study/Travel'] = tafe_df[study_travel_col].any(axis=1)
after = pd.concat([tafe_df[study_travel_col], tafe_df['Study/Travel']], axis=1)

# make age naming convention match dete_df
tafe_df['CurrentAge.     Current Age'] = tafe_df['CurrentAge.     Current Age'].str.replace(' – ', '-')

# change column names on tafe to match dete
header_dict ={
    'CESSATION YEAR': 'Cease Date',
    'Classification.     Classification': 'Classification',
    'Contributing Factors. Career Move - Private Sector ': 'Career move to private sector',
    'Contributing Factors. Career Move - Public Sector ': 'Career move to public sector',
    'Contributing Factors. Dissatisfaction': 'Job dissatisfaction',
    'Contributing Factors. Ill Health': 'Ill Health',
    'Contributing Factors. Interpersonal Conflict': 'Interpersonal conflicts',
    'Contributing Factors. Maternity/Family': 'Maternity/family',
    'CurrentAge.     Current Age': 'Age',
    'Employment Type.     Employment Type': 'Employment Status',
    'Gender.     What is your Gender?': 'Gender',
    'Institute': 'Region',
    'InstituteViews. Topic:1. I feel the senior leadership had a clear vision and direction': 'Performance of supervisor',
    'InstituteViews. Topic:2. I was given access to skills training to help me do my job better': 'Professional Development',
    'InstituteViews. Topic:3. I was given adequate opportunities for personal development': 'Further PD',
    'InstituteViews. Topic:4. I was given adequate opportunities for promotion within %Institute]Q25LBL%': 'Opportunities for promotion',
    'InstituteViews. Topic:9. I was kept informed of the changes in the organisation which would affect me': 'Kept informed',
    'LengthofServiceCurrent. Length of Service at current workplace (in years)': 'LengthofServiceCurrent',
    'LengthofServiceOverall. Overall Length of Service at Institute (in years)': 'LengthofServiceOverall',
    'Reason for ceasing employment': 'SeparationType',
    'Record ID': 'ID',
    'WorkUnitViews. Topic:19. I was given adequate support and co-operation by my peers to enable me to do my job': 'Peer support',
    'WorkUnitViews. Topic:20. I was able to use the full range of my skills in my job': 'Skills',
    'WorkUnitViews. Topic:24. I was able to cope with the level of stress and pressure in my job': 'Stress and pressure support',
    'WorkUnitViews. Topic:25. My job allowed me to balance the demands of work and family to my satisfaction': 'Worklife balance',
    'WorkUnitViews. Topic:26. My supervisor gave me adequate personal recognition and feedback on my performance': 'Feedback',
    'WorkUnitViews. Topic:27. My working environment was satisfactory e.g. sufficient space, good lighting, suitable seating and working area': 'Physical environment',
    'WorkUnitViews. Topic:28. I was given the opportunity to mentor and coach others in order for me to pass on my skills and knowledge prior to my cessation date': 'Coach',
    'WorkUnitViews. Topic:29. There was adequate communication between staff in my unit': 'Communication',
    'WorkUnitViews. Topic:30. Staff morale was positive within my work unit': 'Staff morale'
}
tafe_df.rename(columns=header_dict, inplace=True)

# ------merged both dfs-----

# merge both df's
merged_df = pd.concat([dete_df, tafe_df], join='inner')
# merged_df.to_excel('C:/Users/jason/personal_projects/DataScience/Clean And Analyze Employee Exit Surveys/merged_df.xlsx', index=False)

# save to excel file
# merged_preview_clean = df_column_summary(merged_df)
# merged_preview_clean.to_excel('C:/Users/jason/personal_projects/DataScience/Clean And Analyze Employee Exit Surveys/header_summary/merged_exit_survey_header_summary.xlsx', index=False)

# table of nulls by source
source_null_grp = merged_df.groupby('source').count().transpose()

# visual of nulls by source
# merged_graph = merged_df.set_index('source')
# plot = sns.heatmap(merged_graph.isnull(), cbar=False)
# plt.show()

# ------merged cleaning and restructure dataset to optimize for further cleaning and visuals-----
# melt contributing columns
contributing_cols = ['Career move to public sector', 'Career move to private sector', 'Interpersonal conflicts',
                     'Job dissatisfaction', 'Maternity/family', 'Study/Travel', 'Ill Health']
non_contributing_col = [col for col in list(merged_df.columns) if col not in contributing_cols]

merged_melt_df = pd.melt(merged_df, id_vars=non_contributing_col, value_vars=contributing_cols,
                         var_name='contributing_factors', value_name='contributing_values')

# replace true and false with 0, 1
merged_melt_df['contributing_values'] = merged_melt_df['contributing_values'].replace({True: 1, False: 0})

# melt likert columns
likert_cols = ['Professional Development', 'Opportunities for promotion', 'Staff morale', 'Physical environment',
               'Worklife balance', 'Stress and pressure support', 'Performance of supervisor', 'Peer support',
               'Skills', 'Coach', 'Feedback', 'Further PD', 'Communication', 'Kept informed']
non_likert_col = [col for col in list(merged_melt_df.columns) if col not in likert_cols]

merged_melt_df = pd.melt(merged_melt_df, id_vars=non_likert_col, value_vars=likert_cols,
                         var_name='likert_factors', value_name='likert_values')
merged_melt_df['likert_values'] = merged_melt_df['likert_values'].replace(
    {
        'Strongly Agree': 2,
        'Agree': 1,
        'Neutral': 0,
        'Disagree': -1,
        'Strongly Disagree': -2,
        'M': np.nan, # todo find out what 'M' stands for
        'Not Applicable': np.nan
    }
)

# melt service length columns
service_length_cols = ['LengthofServiceOverall', 'LengthofServiceCurrent']
non_service_length_col = [col for col in list(merged_melt_df.columns) if col not in service_length_cols]

merged_melt_df = pd.melt(merged_melt_df, id_vars=non_service_length_col, value_vars=service_length_cols,
                         var_name='service_length_factors', value_name='service_length_values')

# merged_melt_df.to_excel('C:/Users/jason/personal_projects/DataScience/Clean And Analyze Employee Exit Surveys/merged_melt_df.xlsx', index=False)

# ------Analysis-----

# todo stacked bar chart for likert that sums values
likert_colors = ['white', 'firebrick', 'lightcoral', 'gainsboro', 'cornflowerblue', 'darkblue']
# grp = merged_melt_df.groupby(by=['likert_factors', 'likert_values']).count()
pvt = pd.pivot_table(merged_melt_df, values='likert_values', index='likert_factors', columns='likert_values')
grp.plot.bar(stacked=True)

print('stop')
