import os
import numpy as np
import pandas as pd
import sys
sys.path.append("/home1/jialh/brain/01meta/multikingdom")
from scripts.utils.Solve_Imbalanced_Classes import imblearn
from scripts.utils.merge_feature import merge_features_transfer
from scripts.utils.feature_selection import transfer_feature_selection
from collections import Counter

def preprare_train_and_test(workdir, taxon, meta_feats, stage, train_study, test_studies, model, feat_type, fs_method, sampler):
    #print("begin to deal with NC-{} by {}_{}".format(stage, model, train_study))
    meta_feats_filter = meta_feats.loc[(meta_feats['Group'].isin(['NC', stage])),]
    meta_feats_train = None
    if train_study in ['CHN2', 'CHN', 'GER', 'JPN']:
        meta_feats_train = meta_feats_filter.loc[meta_feats_filter['Batch'] == train_study,]
    elif train_study == "CHN+CHN2":
        meta_feats_train = meta_feats_filter.loc[meta_feats_filter['Batch'].isin(["CHN", "CHN2"]),]
    elif train_study == "JPN+GER+CHN":
        meta_feats_train = meta_feats_filter.loc[meta_feats_filter['Batch'].isin(["JPN", "GER", "CHN"]),]
    elif train_study == "JPN+GER+CHN2":
        meta_feats_train = meta_feats_filter.loc[meta_feats_filter['Batch'].isin(["JPN", "GER", "CHN2"]),]
    elif train_study == "CHN+CHN2+GER":
        meta_feats_train = meta_feats_filter.loc[meta_feats_filter['Batch'].isin(["CHN", "CHN2", "GER"]),]
    train_label = meta_feats_train['Group']
    train_label = np.array([0 if i == 'NC' else 1 for i in train_label])
    train_features = meta_feats_train.iloc[:, 14:]
    train_sample_list = train_features.index.values.tolist()
    train_y = train_label.ravel()
    train_features = train_features.fillna(0)
    # print("begin to deal with NC-{} by {}_{}_{}".format(stage, model, feat_type, train_study))
    # print("type(train_features):", type(train_features))
    # train_X, train_feature_list = merge_features(train_features, feat_type)

    ###<-------------------------------->###
    train_features, train_y = imblearn(train_features, train_y, stage, train_study, sampler)

    test_study_dic = {}
    train_X = None
    # train_y = None
    feature_list = None

    n_features_in=0; n_features=0; selected_features=''

    for test_study in test_studies:
        if test_study == train_study:
            continue
        else:
            meta_feats_filter = meta_feats.loc[(meta_feats['Group'].isin(['NC', stage])),]
            meta_feats_test = meta_feats_filter.loc[meta_feats_filter['Batch'] == test_study,]
            ###
            meta_feats_test = meta_feats_test.loc[meta_feats_test.iloc[:, 4:].sum(axis=1) > 0,]
            ###


            test_label = meta_feats_test['Group']
            test_label = np.array([0 if i == 'NC' else 1 for i in test_label])
            test_features = meta_feats_test.iloc[:, 14:]
            test_sample_list = test_features.index.values.tolist()
            test_y = test_label.ravel()
            test_features = test_features.fillna(0)

            ###
            if (train_features.shape[0] > 0) and (test_features.shape[0] > 0):
                test_features, test_y = imblearn(test_features, test_y, stage, test_study, sampler)

                ##merge_features_transfer(train_features_df, test_features_df, feat_type, min_abundance, min_prevalence)
                print("before merge_features_transfer: feat_type: {}, train_features.shape: {}, test_feature.shape: {}.".format(
                    feat_type, train_features.shape, test_features.shape))
                train_X, test_X, feature_list = merge_features_transfer(train_features, test_features, feat_type)
                print("len(feature_list): {}".format(len(feature_list)))
                print("feat_type: {}".format(feat_type))
                if feat_type in ["ABFV+KOs+pathways", 'ABFV+KOs+pathways+ConQuR']:
                    suffix = ''
                    if feat_type == "ABFV+KOs+pathways":
                        suffix = ''
                    elif feat_type == "ABFV+KOs+pathways+ConQuR":
                        suffix = '+ConQuR'
                    print("deal with {}".format(feat_type))
                    merge_feature_list = []
                    train_X_df = pd.DataFrame(data=train_X, index=train_sample_list, columns=feature_list)
                    test_X_df = pd.DataFrame(data=test_X, index=test_sample_list, columns=feature_list)
                    for single_feat_type in ['ABFV', 'KOs', 'pathways']:
                        if single_feat_type == 'ABFV':
                            taxon = 'species' + suffix
                        elif single_feat_type in ['KOs', 'pathways']:
                            taxon = single_feat_type + suffix
                        else:
                            taxon = single_feat_type + suffix
                        cv_prefix = "CV_{}_{}_{}_{}_{}_{}".format(train_study, stage, model, single_feat_type+suffix, fs_method, sampler)
                        feature_importance_file = os.path.join(workdir, "{}_{}".format(train_study, taxon), model,
                                                               "{}_feature_importance.csv".format(cv_prefix))
                        print("feature_importance_file: {}.".format(feature_importance_file))
                        if os.path.exists(feature_importance_file):
                            print("{} exists.".format(feature_importance_file))
                            feature_importance_df = pd.read_csv(feature_importance_file, header=0, index_col=0)
                            single_feature_list = feature_importance_df.index.values.tolist()
                            merge_feature_list = merge_feature_list + single_feature_list
                    ###
                    print("len(merge_feature_list): {}".format(len(merge_feature_list)))
                    train_X_df = train_X_df.loc[:, train_X_df.columns.isin(merge_feature_list)]
                    test_X_df = test_X_df.loc[:, test_X_df.columns.isin(merge_feature_list)]
                    train_X = train_X_df.values
                    test_X = test_X_df.values
                    ##list(set(a) & set(b))
                    feature_list = list(set(train_X_df.columns.values.tolist()) & set(merge_feature_list))
                    print("features after merge ABFV+KOs+pathways: {}".format(feature_list))
                    print("{} features after merge ABFV+KOs+pathways.".format(len(feature_list)))
                    ####
                    n_features_in = len(feature_list)
                    # test_X_df = pd.DataFrame(test_X, index=test_sample_list, columns=test_feature_list)
                    # test_X_df.to_csv(os.path.join(workdir, "testwork", "CHN_A_features.csv"), header=True, index=True)
                    ##函数返回值的数量不一致。
                    if fs_method == "RandomForest+RFECV":
                        train_X, test_X, feature_list = transfer_feature_selection(train_X, train_y, test_X, feature_list,
                                                                                   fs_method="RandomForest+RFECV80")
                    else:
                        train_X, test_X, feature_list = transfer_feature_selection(train_X, train_y, test_X, feature_list,
                                                                                   fs_method="RandomForest+RFECV_X4")
                    n_features = len(feature_list)
                    selected_features = ','.join(feature_list)
                    train_X = np.nan_to_num(train_X, nan=0.0)
                    test_X = np.nan_to_num(test_X, nan=0.0)
                else:
                    n_features_in = len(feature_list)
                    # test_X_df = pd.DataFrame(test_X, index=test_sample_list, columns=test_feature_list)
                    # test_X_df.to_csv(os.path.join(workdir, "testwork", "CHN_A_features.csv"), header=True, index=True)
                    ##函数返回值的数量不一致。
                    train_X, test_X, feature_list = transfer_feature_selection(train_X, train_y, test_X, feature_list, fs_method)
                    n_features = len(feature_list)
                    selected_features = ','.join(feature_list)
                    train_X = np.nan_to_num(train_X, nan=0.0)
                    test_X = np.nan_to_num(test_X, nan=0.0)

                test_study_dic[test_study] = {'test_X': test_X, 'test_y': test_y, 'test_sample_list':test_sample_list, 'test_feature_list':feature_list}
    return train_X, train_sample_list, train_y, test_study_dic, feature_list, n_features_in, n_features, selected_features