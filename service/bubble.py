"""
Service latar belakang Haimiya (bubble overlay).
--------------------------------------------------
File ini dijalankan python-for-android sebagai FOREGROUND SERVICE
(lihat buildozer.spec: services = bubble:service/bubble.py).

Tugasnya:
- Nampilin notifikasi permanen (wajib buat foreground service)
- Nempelin bubble kecil yang bisa di-drag ke WindowManager (overlay
  di atas app lain)
- Kalau bubble di-tap (bukan di-drag), buka lagi activity utama Haimiya

CATATAN JUJUR: kode ini ditulis berdasarkan pola pyjnius + WindowManager
yang umum dipakai buat chat-head di Kivy/python-for-android, tapi belum
pernah dites langsung di HP fisik. Kemungkinan besar akan perlu
debugging (logcat) begitu pertama kali dijalankan.
"""

from jnius import autoclass, cast, PythonJavaClass, java_method

PythonService = autoclass("org.kivy.android.PythonService")
Context = autoclass("android.content.Context")
WindowManager = autoclass("android.view.WindowManager")
LayoutParams = autoclass("android.view.WindowManager$LayoutParams")
PixelFormat = autoclass("android.graphics.PixelFormat")
Gravity = autoclass("android.view.Gravity")
TextView = autoclass("android.widget.TextView")
Color = autoclass("android.graphics.Color")
VERSION = autoclass("android.os.Build$VERSION")
MotionEvent = autoclass("android.view.MotionEvent")
Intent = autoclass("android.content.Intent")
NotificationBuilder = autoclass("android.app.Notification$Builder")
NotificationChannel = autoclass("android.app.NotificationChannel")
NotificationManager = autoclass("android.app.NotificationManager")

CHANNEL_ID = "haimiya_bubble_channel"

service = PythonService.mService


class TouchListener(PythonJavaClass):
    """Nangkep drag (pindahin bubble) vs tap (buka app utama)."""

    __javainterfaces__ = ["android/view/View$OnTouchListener"]
    __javacontext__ = "app"

    def __init__(self, bubble_view, layout_params, window_manager, on_tap):
        super().__init__()
        self.bubble_view = bubble_view
        self.params = layout_params
        self.wm = window_manager
        self.on_tap = on_tap
        self.init_x = 0
        self.init_y = 0
        self.touch_x = 0.0
        self.touch_y = 0.0
        self.moved = False

    @java_method("(Landroid/view/View;Landroid/view/MotionEvent;)Z")
    def onTouch(self, view, event):
        action = event.getAction()
        if action == MotionEvent.ACTION_DOWN:
            self.init_x = self.params.x
            self.init_y = self.params.y
            self.touch_x = event.getRawX()
            self.touch_y = event.getRawY()
            self.moved = False
            return True
        elif action == MotionEvent.ACTION_MOVE:
            dx = event.getRawX() - self.touch_x
            dy = event.getRawY() - self.touch_y
            if abs(dx) > 8 or abs(dy) > 8:
                self.moved = True
            self.params.x = int(self.init_x + dx)
            self.params.y = int(self.init_y + dy)
            self.wm.updateViewLayout(self.bubble_view, self.params)
            return True
        elif action == MotionEvent.ACTION_UP:
            if not self.moved:
                self.on_tap()
            return True
        return False


def build_notification():
    manager = cast(
        NotificationManager, service.getSystemService(Context.NOTIFICATION_SERVICE)
    )
    if VERSION.SDK_INT >= 26:
        channel = NotificationChannel(
            CHANNEL_ID, "Haimiya", NotificationManager.IMPORTANCE_LOW
        )
        manager.createNotificationChannel(channel)
        builder = NotificationBuilder(service, CHANNEL_ID)
    else:
        builder = NotificationBuilder(service)
    builder.setContentTitle("Haimiya aktif")
    builder.setContentText("Bubble Haimiya lagi jalan.")
    builder.setSmallIcon(service.getApplicationInfo().icon)
    return builder.build()


def open_main_activity():
    package_name = service.getPackageName()
    launch_intent = service.getPackageManager().getLaunchIntentForPackage(package_name)
    if launch_intent:
        launch_intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        service.startActivity(launch_intent)


def main():
    service.startForeground(1, build_notification())

    window_manager = cast(WindowManager, service.getSystemService(Context.WINDOW_SERVICE))

    overlay_type = (
        LayoutParams.TYPE_APPLICATION_OVERLAY
        if VERSION.SDK_INT >= 26
        else LayoutParams.TYPE_PHONE
    )

    params = LayoutParams(
        LayoutParams.WRAP_CONTENT,
        LayoutParams.WRAP_CONTENT,
        overlay_type,
        LayoutParams.FLAG_NOT_FOCUSABLE,
        PixelFormat.TRANSLUCENT,
    )
    params.gravity = Gravity.TOP | Gravity.LEFT
    params.x = 0
    params.y = 300

    bubble = TextView(service)
    bubble.setText("H")
    bubble.setTextColor(Color.WHITE)
    bubble.setBackgroundColor(Color.parseColor("#7C4DFF"))
    bubble.setPadding(40, 40, 40, 40)

    listener = TouchListener(bubble, params, window_manager, open_main_activity)
    bubble.setOnTouchListener(listener)

    window_manager.addView(bubble, params)

    from time import sleep

    while True:
        sleep(1)


main()
