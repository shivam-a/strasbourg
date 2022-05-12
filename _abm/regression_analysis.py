import biogeme.biogeme as bio
import biogeme.database as db
import biogeme.models as models
import numpy as np
from sklearn import *
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from daily_activity_pattern import *

# change the root directory to where CONFIG is kept
config = configparser.ConfigParser()
config.read(r'CONFIG.txt')

def _regression_analysis(df: pd.DataFrame, dependent_variable: str, independent_variables: list, option: int, file_name: str, choice_set: str):
    """
    Does the multinomial regression analysis using sklearn
    @param df: dataframe that needs to analysed
    @param dependent_variable: dependent variables for the regression
    @param independent_variables: independent variables for the regression
    @param option: different options
    @param file_name: name of the file
    @param choice_set: the choice that one wants to keep in the choice set (used mainly for tour_chain_rank)
    """
    if option == 1:
        keep_variables = [*socio_economic_attributes, dependent_variable]
        find_dummy(df, keep_variables)
        df = df.filter(regex='|'.join([*keep_variables, dependent_variable, *independent_variables]))
    elif option == 2:
        keep_variables = socio_economic_attributes
        find_dummy(df, keep_variables)
        df = df.filter(regex='|'.join([*keep_variables, dependent_variable, *independent_variables]))
    elif option == 3:
        keep_variables = ['age', 'license', 'hh_income']
        find_dummy(df, keep_variables)
        df = df.filter(regex='|'.join([*keep_variables, dependent_variable, *independent_variables]))
    else:
        df = df.filter(regex='|'.join([dependent_variable, *independent_variables]))
    df.to_csv(
        config['ANALYSIS']['dummy'] + file_name + '_dummy_df.csv',
        index=False)
    earlier = len(df)
    df = df[df[dependent_variable].astype(str).str.contains(choice_set)]
    later = len(df)
    print('reduction of choice set by ', earlier - later, 'values')
    # Independent variables
    X = df.filter(regex='|'.join(independent_variables))
    y = df.loc[:, df.columns == dependent_variable]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    # logistic regression
    mul_lr = linear_model.LogisticRegression(multi_class='multinomial',
                                             solver='newton-cg').fit(X_train, y_train.values.ravel())
    predictions = mul_lr.predict_proba(X_test)
    results = pd.concat([X_test.reset_index(drop=True),
                         y_test.reset_index(drop=True),
                         pd.DataFrame(predictions, columns=mul_lr.classes_),
                         pd.DataFrame([max(i) for i in predictions], columns=['max']),
                         pd.DataFrame(mul_lr.predict(X_test), columns=['Prediction'])], axis=1)
    write_to_excel(results, 'test_result', file_name)
    score = {file_name: mul_lr.score(X_test, y_test)}
    print(score)
    intercept_df = pd.DataFrame(mul_lr.intercept_)
    add_column_index_names(intercept_df, column_list=['Intercept'], index_list=mul_lr.classes_)
    coef_df = pd.DataFrame(mul_lr.coef_)
    add_column_index_names(coef_df, column_list=X_train.columns, index_list=mul_lr.classes_)
    cm_df = pd.DataFrame(metrics.confusion_matrix(y_test, mul_lr.predict(X_test)))
    V = X_train.values.dot(mul_lr.coef_.transpose())
    U = V + mul_lr.intercept_
    A = np.exp(U)
    P = A / (1 + A)
    P /= P.sum(axis=1).reshape((-1, 1))
    V_df = pd.DataFrame(V)
    print(classification_report(y_test, mul_lr.predict(X_test)))
    add_column_index_names(V_df, column_list=mul_lr.classes_, index_list=None)
    A_df = pd.DataFrame(A)
    add_column_index_names(A_df, column_list=mul_lr.classes_, index_list=None)
    P_df = pd.DataFrame(P)
    add_column_index_names(P_df, column_list=mul_lr.classes_, index_list=None)
    write_to_excel(intercept_df, 'intercept', file_name)
    write_to_excel(coef_df, 'coefficient', file_name)
    write_to_excel(cm_df, 'confusion', file_name)
    write_to_excel(V_df, 'deterministic', file_name)
    write_to_excel(A_df, 'utility', file_name)
    write_to_excel(P_df, 'probability', file_name)


def find_dummy(df, keep_variables):
    """
    To make the variables into dummy variables to make categorical variables to numeric (0 and 1)
    @param df: the dataframe that needs to have dummy variables
    @param keep_variables: the variables needed to made into dummy
    @return: dataframe with columns with dummy variables
    """
    label = preprocessing.LabelEncoder()
    for col in keep_variables:
        n = len(df[col].unique())
        if n > 1:
            X = pd.get_dummies(df[col], prefix=col, drop_first=True)
            # X = X.drop(X.columns[0], axis = 1)
            df[X.columns] = X
            if col in socio_economic_attributes:
                df.drop(col, axis=1, inplace=True)  # drop the original categorical variable (optional)
        else:
            label.fit(df[col])
            df[col] = label.transform(df[col])


def write_to_excel(dataframe: pd.DataFrame, description: str, file_name: str):
    """
    Writes the dataframe into an excel format
    @param dataframe: dataframe that is to be converted to excel
    @param description: type of file (coefficient, intercept, utilities...)
    @param file_name: name of the file describing the chain type and condensed form
    """
    writer = pd.ExcelWriter(
        config['ANALYSIS']['regression'] + file_name + '_' + description + '.xlsx',
        engine='xlsxwriter')
    dataframe.to_excel(writer)
    writer.save()
    print(description, 'of', file_name, 'dataframe was generated successfully')


def add_column_index_names(dataframe: pd.DataFrame, index_list = None, column_list = None):
    """
    Takes the dataframe and changes the column or index into whatever list is passed as parameter
    @param dataframe: dataframe that needs to change index|column
    @param index_list: list that makes the index of the dataframe meaningful
    @param column_list: list that makes the column of the dataframe meaningful
    """
    if column_list is not None:
        dataframe.columns = column_list
    if index_list is not None:
        dataframe.index = index_list

# Not used
def _biogeme_logit_tour_rank():
    keep_variables = [*socio_economic_attributes, 'tour_chain_rank']
    label = preprocessing.LabelEncoder()
    # df = pd.read_csv(
    #     config['DAP']['datasets'] + chain + '_' + density + '_chain_df.csv',
    #     index_col=0).dropna().reset_index()
    df = pd.read_csv(
        config['DAP']['datasets'] + 'tour_condensed_chain_df.csv',
        index_col=0).dropna().reset_index()
    # df[chain + '_chain'] = df[chain + '_chain'].astype('category').cat.codes
    for col in df.filter(like='chain').columns:
        df[col] = label.fit_transform(df[col])
    for col in keep_variables:
        n = len(df[col].unique())
        if n > 1:
            if col == 'tour_chain_rank':
                X = pd.get_dummies(df[col], prefix=col)
                # X = X.drop(X.columns[0], axis = 1)
                df[X.columns] = X
            else:
                X = pd.get_dummies(df[col], prefix=col, drop_first=True)
                # X = X.drop(X.columns[0], axis = 1)
                df[X.columns] = X
                df.drop(col, axis=1, inplace=True)  # drop the original categorical variable (optional)
        else:
            label.fit(df[col])
            df[col] = label.transform(df[col])
    df = df.filter(regex='|'.join(keep_variables))
    df = df.loc[:, ~df.columns.duplicated()]
    database = db.Database('dataframe', df)
    globals().update(database.variables)
    intercept = {}
    coefficient = {}
    utilities = {}
    additional = []
    V = {}
    av = {}
    for i in df['tour_chain_rank'].unique():
        if i == 0:
            intercept['ASC_{}'.format(i)] = 'Beta(\'ASC_{}\', 0, None, None, 1)'.format(i)
        intercept['ASC_{}'.format(i)] = 'Beta(\'ASC_{}\', 0, None, None, 0)'.format(i)
    for k, v in intercept.items():
        intercept[k] = eval(v)
    globals().update(intercept)
    for i in df.filter(regex='|'.join(socio_economic_attributes)).columns:
        coefficient['B_{}'.format(i)] = 'Beta(\'B_{}\', 0, None, None, 0)'.format(i)
    for k, v in coefficient.items():
        coefficient[k] = eval(v)
    globals().update(coefficient)
    for i in df.filter(regex='|'.join(socio_economic_attributes)).columns:
        additional.append('B_{} * {}'.format(i, i))
    for i in df['tour_chain_rank'].unique():
        utilities['V{}'.format(i)] = 'ASC_{} + '.format(i) + (' + '.join(additional))
    for k, v in utilities.items():
        utilities[k] = eval(v)
    globals().update(utilities)
    for i in df['tour_chain_rank'].unique():
        V[i] = 'V{}'.format(i)
    for k, v in V.items():
        V[k] = eval(v)
    globals().update(V)
    # for i in df['tour_chain_rank'].unique():
    #     availabilities['tour_chain_rank_' + str(i)] = 'tour_chain_rank_' + str(i)
    # for k, v in availabilities.items():
    #     availabilities[k] = eval(v)
    # globals().update(availabilities)
    for i in df['tour_chain_rank'].unique():
        av[i] = 'tour_chain_rank_' + str(i)
    for k, v in av.items():
        av[k] = eval(v)
    globals().update(av)
    print(av)
    log_prob = models.loglogit(V, av, tour_chain_rank)
    biogeme = bio.BIOGEME(database, log_prob)
    biogeme.modelName = '01logit'
    results = biogeme.estimate()
    print(results)
    # print(coefficient)
    # print(additional)
    # print(utilities)
    print(database.variables)
    # print(V)
    # print(av)
    # print(availabilities)