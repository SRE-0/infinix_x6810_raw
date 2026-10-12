package org.x6810.resolutionprobe;
import android.app.Activity;
import android.os.*;
import android.hardware.camera2.*;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.*;
import android.util.*;
import android.widget.TextView;
import java.util.*;
import java.util.concurrent.*;
import java.io.*;
import java.nio.ByteBuffer;

/** Explicit normal/HD enumeration and optional single direct capture. */
public class ProbeActivity extends Activity {
    HandlerThread thread; Handler handler; TextView view;
    StringBuilder report = new StringBuilder();
    CameraDevice device; CameraCaptureSession session; ImageReader reader;
    void record(String s) {
        Log.i("ResolutionProbe", s);
        synchronized(report) { report.append(s).append('\n'); }
        runOnUiThread(() -> view.setText(report.toString()));
    }
    public void onCreate(Bundle state) {
        super.onCreate(state); view = new TextView(this); setContentView(view);
        thread = new HandlerThread("ResolutionProbe"); thread.start();
        handler = new Handler(thread.getLooper()); new Thread(() -> probe()).start();
    }
    void probe() {
        String id = getIntent().getStringExtra("camera"); if(id == null) id = "0";
        String label = getIntent().getStringExtra("label");
        if(label == null || !label.matches("[A-Za-z0-9_-]+")) label = "result";
        boolean capture = getIntent().getBooleanExtra("capture", false);
        int format = getIntent().getIntExtra("format", 256);
        int width = getIntent().getIntExtra("width", 8000), height = getIntent().getIntExtra("height", 6000);
        try {
            CameraManager manager = (CameraManager)getSystemService(CAMERA_SERVICE);
            CameraCharacteristics c = manager.getCameraCharacteristics(id);
            StreamConfigurationMap map = c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            record("camera=" + id + " active=" + c.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE));
            for(int f : new int[]{256, 35, 32, 34}) {
                record("format=" + f + " normal=" + Arrays.toString(map.getOutputSizes(f)));
                record("format=" + f + " highResolution=" + Arrays.toString(map.getHighResolutionOutputSizes(f)));
            }
            if(capture) {
                Size target = new Size(width, height);
                List<Size> supported = new ArrayList<>();
                Size[] normal = map.getOutputSizes(format), hd = map.getHighResolutionOutputSizes(format);
                if(normal != null) supported.addAll(Arrays.asList(normal));
                if(hd != null) supported.addAll(Arrays.asList(hd));
                if(!supported.contains(target)) throw new Exception("Not advertised: " + target + " format=" + format);
                record("requested=" + target + " format=" + format + " minimumNs=" + map.getOutputMinFrameDuration(format, target));
                CompletableFuture<CameraDevice> opened = new CompletableFuture<>();
                manager.openCamera(id, new CameraDevice.StateCallback() {
                    public void onOpened(CameraDevice d) { device=d; opened.complete(d); }
                    public void onDisconnected(CameraDevice d) { d.close(); opened.completeExceptionally(new Exception("disconnected")); }
                    public void onError(CameraDevice d, int error) { d.close(); opened.completeExceptionally(new Exception("open="+error)); }
                }, handler);
                opened.get(15, TimeUnit.SECONDS);
                reader = ImageReader.newInstance(width, height, format, 2);
                BlockingQueue<Image> images = new ArrayBlockingQueue<>(2);
                reader.setOnImageAvailableListener(r -> { Image i=r.acquireNextImage(); if(i!=null&&!images.offer(i))i.close(); }, handler);
                CompletableFuture<CameraCaptureSession> configured = new CompletableFuture<>();
                device.createCaptureSession(Arrays.asList(reader.getSurface()), new CameraCaptureSession.StateCallback() {
                    public void onConfigured(CameraCaptureSession s) { session=s; configured.complete(s); }
                    public void onConfigureFailed(CameraCaptureSession s) { s.close(); configured.completeExceptionally(new Exception("configure failed")); }
                }, handler);
                configured.get(20, TimeUnit.SECONDS);
                CaptureRequest.Builder request = device.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
                request.addTarget(reader.getSurface());
                CompletableFuture<TotalCaptureResult> captured = new CompletableFuture<>();
                long start = SystemClock.elapsedRealtime();
                session.capture(request.build(), new CameraCaptureSession.CaptureCallback() {
                    public void onCaptureCompleted(CameraCaptureSession s, CaptureRequest q, TotalCaptureResult r) { captured.complete(r); }
                    public void onCaptureFailed(CameraCaptureSession s, CaptureRequest q, CaptureFailure f) { captured.completeExceptionally(new Exception("capture="+f.getReason())); }
                }, handler);
                TotalCaptureResult result = captured.get(30, TimeUnit.SECONDS);
                Image image = images.poll(15, TimeUnit.SECONDS);
                if(image == null) throw new Exception("image timeout");
                try {
                    record("image="+image.getWidth()+"x"+image.getHeight()+" format="+image.getFormat()+" elapsedMs="+(SystemClock.elapsedRealtime()-start));
                    record("timestamp="+image.getTimestamp()+" resultTimestamp="+result.get(CaptureResult.SENSOR_TIMESTAMP)+" crop="+result.get(CaptureResult.SCALER_CROP_REGION));
                    if(image.getWidth()!=width||image.getHeight()!=height) throw new Exception("dimension mismatch");
                    if(!Long.valueOf(image.getTimestamp()).equals(result.get(CaptureResult.SENSOR_TIMESTAMP))) throw new Exception("timestamp mismatch");
                    for(int p=0;p<image.getPlanes().length;p++) {
                        Image.Plane plane=image.getPlanes()[p]; ByteBuffer buffer=plane.getBuffer(); byte[] bytes=new byte[buffer.remaining()];buffer.get(bytes);
                        record("plane="+p+" bytes="+bytes.length+" rowStride="+plane.getRowStride()+" pixelStride="+plane.getPixelStride());
                        if(bytes.length==0) throw new Exception("empty plane");
                        try(FileOutputStream f=new FileOutputStream(new File(getExternalFilesDir(null), label+(format==256?".jpg":"-plane"+p+".bin")))) { f.write(bytes); }
                    }
                } finally { image.close(); }
                Image extra; while((extra=images.poll())!=null)extra.close();
            }
            record("PASS " + label + " (delivery only; native detail not asserted)");
        } catch(Throwable e) { record("FAIL " + label + " " + Log.getStackTraceString(e)); }
        finally {
            if(session!=null)session.close(); if(device!=null)device.close(); if(reader!=null)reader.close(); thread.quitSafely();
            try(FileOutputStream f=new FileOutputStream(new File(getExternalFilesDir(null), label+".txt"))) { f.write(report.toString().getBytes("UTF-8")); }
            catch(Exception e) { Log.e("ResolutionProbe","save",e); }
        }
    }
}
