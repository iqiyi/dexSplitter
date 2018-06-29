package com.example.far;

import android.app.Activity;
import android.os.Bundle;
import android.support.annotation.Nullable;
import android.util.Log;

import org.greenrobot.greendao.DaoException;


public class FarActivity extends Activity {
    private String TAG = "FarActivity";
    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_far);
        Log.i(TAG,FarClass1.Test());
        DaoException daoException = new DaoException("green dao exception..");
        Log.i(TAG,daoException.getMessage());
    }

}
