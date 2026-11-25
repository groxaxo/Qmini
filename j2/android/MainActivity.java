package com.qmini.j2;
import android.Manifest;
import android.app.Activity;
import android.os.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.hardware.Camera;
import android.speech.tts.TextToSpeech;
import android.view.*;
import android.widget.*;
import java.util.Locale;
import java.net.*;
import java.io.*;
import org.json.JSONObject;

public class MainActivity extends Activity {
    private Face face; private FrameLayout stage; private TextView status;
    private TextToSpeech tts; private boolean ttsReady,preview; private Camera cam; private SurfaceView surface;
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        LinearLayout layout=new LinearLayout(this);layout.setOrientation(1);layout.setBackgroundColor(Color.rgb(9,15,24));
        stage=new FrameLayout(this);face=new Face();stage.addView(face);
        layout.addView(stage,new LinearLayout.LayoutParams(-1,0,1));
        status=new TextView(this);status.setTextColor(Color.WHITE);status.setTextSize(13);
        status.setPadding(12,2,12,2);status.setText("Qmini J2 | local head | motors disconnected");layout.addView(status);
        LinearLayout buttons=new LinearLayout(this);
        button(buttons,"Connect",()->connect());
        button(buttons,"Speak",()->speak());
        button(buttons,"Camera",()->toggleCamera());
        button(buttons,"Face",()->stopCamera());
        layout.addView(buttons);setContentView(layout);
        tts=new TextToSpeech(this,result->{if(result==TextToSpeech.SUCCESS){ttsReady=true;tts.setLanguage(Locale.getDefault());}});
        getWindow().getDecorView().setSystemUiVisibility(5894);
    }
    private void button(LinearLayout row,String text,Runnable f){
        Button b=new Button(this);b.setText(text);b.setAllCaps(false);
        row.addView(b,new LinearLayout.LayoutParams(0,-2,1));b.setOnClickListener(v->f.run());
    }
    private void connect(){
        LinearLayout form=new LinearLayout(this);form.setOrientation(1);form.setPadding(16,0,16,0);
        EditText address=new EditText(this);address.setSingleLine(true);address.setHint("http://host:8769");form.addView(address);
        EditText token=new EditText(this);token.setSingleLine(true);token.setInputType(129);token.setHint("Gateway token (not stored)");form.addView(token);
        new android.app.AlertDialog.Builder(this).setTitle("Read-only simulator")
            .setMessage("Use HTTPS or an isolated trusted LAN. No motor commands are supported.").setView(form)
            .setPositiveButton("Check",(d,w)->{
                String raw=address.getText().toString().trim(),key=token.getText().toString().trim();
                try{
                    URI u=new URI(raw);
                    if(!("http".equals(u.getScheme())||"https".equals(u.getScheme()))||u.getHost()==null||u.getUserInfo()!=null||u.getQuery()!=null||u.getFragment()!=null||!((u.getPath()==null)||u.getPath().isEmpty()||"/".equals(u.getPath()))||key.length()<24||key.length()>256)throw new Exception();
                    status.setText("Checking simulation gateway...");
                    new Thread(()->checkGateway(raw.replaceAll("/+$",""),key),"qmini-status").start();
                }catch(Exception e){status.setText("Invalid URL or token");}
            }).setNegativeButton("Cancel",null).show();
    }
    private void checkGateway(String base,String key){
        String message="Gateway unavailable | motors disconnected";HttpURLConnection c=null;
        try{
            c=(HttpURLConnection)new URL(base+"/v1/status").openConnection();
            c.setConnectTimeout(1800);c.setReadTimeout(1800);c.setInstanceFollowRedirects(false);
            c.setRequestProperty("Authorization","Bearer "+key);
            if(c.getResponseCode()==200){
                ByteArrayOutputStream data=new ByteArrayOutputStream();
                try(InputStream in=c.getInputStream()){byte[] buf=new byte[512];int n;
                    while((n=in.read(buf))!=-1){if(data.size()+n>4096)throw new IOException("oversize");data.write(buf,0,n);}}
                JSONObject j=new JSONObject(data.toString("UTF-8"));
                if(j.optString("mode").equals("simulation")&&!j.optBoolean("motors_enabled",true)&&!j.optBoolean("hardware_connected",true))
                    message="Simulation gateway OK | motors disconnected";
                else message="Unsupported gateway | no motor control";
            }
        }catch(Exception ignored){}finally{if(c!=null)c.disconnect();}
        final String result=message;runOnUiThread(()->{if(!isFinishing()&&!isDestroyed())status.setText(result);});
    }
    private void speak(){
        if(ttsReady)tts.speak("Hello! I am Qmini.",TextToSpeech.QUEUE_FLUSH,null,"hello");
        else Toast.makeText(this,"Android text-to-speech unavailable",Toast.LENGTH_SHORT).show();
    }
    private void toggleCamera(){
        if(preview){stopCamera();return;}
        if(Build.VERSION.SDK_INT>=23&&checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{Manifest.permission.CAMERA},1);return;}
        startCamera();
    }
    @Override public void onRequestPermissionsResult(int r,String[] p,int[] g){
        super.onRequestPermissionsResult(r,p,g);if(r==1&&g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED)startCamera();
    }
    private void startCamera(){
        if(preview)return;preview=true;face.setVisibility(View.GONE);surface=new SurfaceView(this);stage.addView(surface,new FrameLayout.LayoutParams(-1,-1));
        surface.getHolder().addCallback(new SurfaceHolder.Callback(){
            public void surfaceCreated(SurfaceHolder h){
                try{
                    if(!preview||surface==null||surface.getHolder()!=h)return;
                    int id=-1;Camera.CameraInfo info=new Camera.CameraInfo();
                    for(int i=0;i<Camera.getNumberOfCameras();i++){Camera.getCameraInfo(i,info);if(info.facing==Camera.CameraInfo.CAMERA_FACING_FRONT){id=i;break;}}
                    if(id<0)throw new Exception("No front camera");cam=Camera.open(id);
                    Camera.getCameraInfo(id,info);int rotation=getWindowManager().getDefaultDisplay().getRotation();
                    int degrees=rotation==Surface.ROTATION_90?90:rotation==Surface.ROTATION_180?180:rotation==Surface.ROTATION_270?270:0;
                    cam.setDisplayOrientation((360-(info.orientation+degrees)%360)%360);
                    Camera.Parameters par=cam.getParameters();Camera.Size best=null;
                    for(Camera.Size sz:par.getSupportedPreviewSizes())if(sz.width<=640&&sz.height<=480&&(best==null||sz.width*sz.height>best.width*best.height))best=sz;
                    if(best!=null){par.setPreviewSize(best.width,best.height);cam.setParameters(par);}
                    cam.setPreviewDisplay(h);cam.startPreview();
                }catch(Exception ex){stopCamera();Toast.makeText(MainActivity.this,"Front camera unavailable",Toast.LENGTH_SHORT).show();}
            }
            public void surfaceChanged(SurfaceHolder h,int f,int w,int hh){}
            public void surfaceDestroyed(SurfaceHolder h){releaseCamera();}
        });
    }
    private void releaseCamera(){if(cam!=null){try{cam.stopPreview();}catch(Exception ignored){}cam.release();cam=null;}}
    private void stopCamera(){releaseCamera();preview=false;if(surface!=null){stage.removeView(surface);surface=null;}face.setVisibility(View.VISIBLE);}
    @Override protected void onPause(){stopCamera();super.onPause();}
    @Override protected void onDestroy(){if(tts!=null)tts.shutdown();super.onDestroy();}
    class Face extends View{
        private final Paint p=new Paint(3);
        Face(){super(MainActivity.this);}
        @Override protected void onDraw(Canvas c){
            c.drawColor(Color.rgb(9,15,24));float w=getWidth(),h=getHeight();long t=SystemClock.uptimeMillis()%4200;
            float open=t<180?.12f:1f;float eh=h*.18f*open;
            p.setColor(Color.rgb(117,221,255));
            for(float x:new float[]{w*.33f,w*.67f})c.drawRoundRect(new RectF(x-w*.09f,h*.42f-eh,x+w*.09f,h*.42f+eh),w*.045f,w*.045f,p);
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(5);p.setStrokeCap(Paint.Cap.ROUND);
            c.drawArc(new RectF(w*.44f,h*.54f,w*.56f,h*.72f),15,150,false,p);p.setStyle(Paint.Style.FILL);
            postInvalidateDelayed(100);
        }
    }
}
