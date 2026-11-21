package com.shahriyarsojibhasan.shahriyarlivetv.utils;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import com.shahriyarsojibhasan.shahriyarlivetv.R;

public class ToastUtils {
    public static void showToast(Context context, String message, boolean isError) {
        LayoutInflater inflater = LayoutInflater.from(context);
        View layout = inflater.inflate(R.layout.custom_toast, null);
        
        TextView text = layout.findViewById(R.id.toast_text);
        text.setText(message);
        
        View root = layout.findViewById(R.id.toast_root);
        if (isError) {
            root.setBackgroundResource(R.drawable.toast_error_background);
        }

        Toast toast = new Toast(context);
        toast.setDuration(Toast.LENGTH_SHORT);
        toast.setView(layout);
        toast.show();
    }
}
