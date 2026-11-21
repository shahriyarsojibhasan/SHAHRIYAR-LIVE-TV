package com.shahriyarsojibhasan.shahriyarlivetv.ui;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.os.SystemClock;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

public class SpringProgressDrawable extends Drawable {
    private final Paint stripePaint;
    private final Paint bgPaint;
    private float offset = 0;
    private final float stripeWidth = 40f;
    private final float stripeSpacing = 40f;

    public SpringProgressDrawable(int bgColor, int stripeColor) {
        bgPaint = new Paint();
        bgPaint.setColor(bgColor);
        bgPaint.setStyle(Paint.Style.FILL);

        stripePaint = new Paint();
        stripePaint.setColor(stripeColor);
        stripePaint.setStyle(Paint.Style.FILL);
        stripePaint.setAntiAlias(true);
    }

    @Override
    public void draw(@NonNull Canvas canvas) {
        Rect bounds = getBounds();
        canvas.drawRect(bounds, bgPaint);

        canvas.save();
        canvas.clipRect(bounds);

        float totalWidth = stripeWidth + stripeSpacing;
        offset = (SystemClock.uptimeMillis() % 1000) / 1000f * totalWidth;

        for (float x = -totalWidth; x < bounds.width() + totalWidth; x += totalWidth) {
            drawStripe(canvas, x + offset, bounds);
        }

        canvas.restore();
        invalidateSelf();
    }

    private void drawStripe(Canvas canvas, float x, Rect bounds) {
        Path path = new Path();
        path.moveTo(x, bounds.top);
        path.lineTo(x + stripeWidth, bounds.top);
        path.lineTo(x + stripeWidth - bounds.height(), bounds.bottom);
        path.lineTo(x - bounds.height(), bounds.bottom);
        path.close();
        canvas.drawPath(path, stripePaint);
    }

    @Override
    public void setAlpha(int alpha) {
        stripePaint.setAlpha(alpha);
    }

    @Override
    public void setColorFilter(@Nullable ColorFilter colorFilter) {
        stripePaint.setColorFilter(colorFilter);
    }

    @Override
    public int getOpacity() {
        return PixelFormat.TRANSLUCENT;
    }
}
