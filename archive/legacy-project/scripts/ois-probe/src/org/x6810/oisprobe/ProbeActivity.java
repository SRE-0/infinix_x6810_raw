package org.x6810.oisprobe;
import android.app.Activity;
import android.os.*;
import android.hardware.camera2.*;
import android.media.*;
import android.graphics.ImageFormat;
import android.util.Log;
import android.widget.TextView;
import java.util.*;
import java.util.concurrent.*;
import java.io.*;
public class ProbeActivity extends Activity {
 HandlerThread thread; Handler handler; TextView view;
 StringBuilder report=new StringBuilder(); CameraDevice device; CameraCaptureSession session; ImageReader reader;
 void log(String s){Log.i("OISProbe",s);synchronized(report){report.append(s).append('\n');}runOnUiThread(()->view.setText(report.toString()));}
 public void onCreate(Bundle state){super.onCreate(state);view=new TextView(this);setContentView(view);thread=new HandlerThread("OISProbe");thread.start();handler=new Handler(thread.getLooper());new Thread(()->runProbe()).start();}
 void runProbe(){String id=getIntent().getStringExtra("camera");if(id==null)id="2";
  try{
   CameraManager manager=(CameraManager)getSystemService(CAMERA_SERVICE);CameraCharacteristics c=manager.getCameraCharacteristics(id);
   log("camera="+id+" modes="+Arrays.toString(c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION)));
   log("oisData="+Arrays.toString(c.get(CameraCharacteristics.STATISTICS_INFO_AVAILABLE_OIS_DATA_MODES)));
   CompletableFuture<CameraDevice> opened=new CompletableFuture<>();
   manager.openCamera(id,new CameraDevice.StateCallback(){public void onOpened(CameraDevice d){opened.complete(d);}public void onDisconnected(CameraDevice d){d.close();opened.completeExceptionally(new Exception("disconnected"));}public void onError(CameraDevice d,int e){d.close();opened.completeExceptionally(new Exception("open "+e));}},handler);
   device=opened.get(15,TimeUnit.SECONDS);reader=ImageReader.newInstance(640,480,ImageFormat.YUV_420_888,3);
   reader.setOnImageAvailableListener(r->{try(Image i=r.acquireLatestImage()){}},handler);
   CompletableFuture<CameraCaptureSession> configured=new CompletableFuture<>();
   device.createCaptureSession(Arrays.asList(reader.getSurface()),new CameraCaptureSession.StateCallback(){public void onConfigured(CameraCaptureSession s){configured.complete(s);}public void onConfigureFailed(CameraCaptureSession s){configured.completeExceptionally(new Exception("configure"));}},handler);
   session=configured.get(20,TimeUnit.SECONDS);
   CaptureRequest.Key<Integer> vendor=null;for(CaptureRequest.Key<?> key:c.getAvailableCaptureRequestKeys())if(key.getName().equals("com.transsion.tranOisMode"))vendor=(CaptureRequest.Key<Integer>)key;
   int[] standards={0,1,0,0,0,0};int[] vendors={-1,-1,-1,1,3,1};
   boolean standardOnly=getIntent().getBooleanExtra("standardOnly",false);
   for(int step=0;step<(standardOnly?3:6);step++){
    final int n=step;CaptureRequest.Builder b=device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);b.addTarget(reader.getSurface());
    b.set(CaptureRequest.CONTROL_VIDEO_STABILIZATION_MODE,0);b.set(CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE,standards[step]);
    if(vendors[step]>=0){if(vendor==null)throw new Exception("missing vendor request key");b.set(vendor,vendors[step]);}
    log("STEP="+n+" requestStandard="+standards[n]+" requestVendor="+(vendor==null?"absent":b.get(vendor)));
    CountDownLatch frames=new CountDownLatch(45);java.util.concurrent.atomic.AtomicInteger count=new java.util.concurrent.atomic.AtomicInteger();
    long start=SystemClock.elapsedRealtime();
    session.setRepeatingRequest(b.build(),new CameraCaptureSession.CaptureCallback(){
     public void onCaptureCompleted(CameraCaptureSession s,CaptureRequest req,TotalCaptureResult r){int k=count.incrementAndGet();if(k==1||k==45)log("STEP="+n+" frame="+k+" resultStandard="+r.get(CaptureResult.LENS_OPTICAL_STABILIZATION_MODE)+" ts="+r.get(CaptureResult.SENSOR_TIMESTAMP));frames.countDown();}
     public void onCaptureFailed(CameraCaptureSession s,CaptureRequest req,CaptureFailure f){log("CAPTURE_FAIL step="+n+" reason="+f.getReason());}
    },handler);
    if(!frames.await(12,TimeUnit.SECONDS))throw new Exception("frame timeout step="+step);
    long remaining=4000-(SystemClock.elapsedRealtime()-start);if(remaining>0)Thread.sleep(remaining);
   }
   log("COMPLETED (request/result evidence; not an optical effectiveness assertion)");
  }catch(Throwable e){log("FAIL "+Log.getStackTraceString(e));}
  finally{if(session!=null)session.close();if(device!=null)device.close();if(reader!=null)reader.close();thread.quitSafely();try(FileOutputStream f=new FileOutputStream(new File(getExternalFilesDir(null),"result.txt"))){f.write(report.toString().getBytes("UTF-8"));}catch(Exception e){Log.e("OISProbe","write",e);}}
 }
}
