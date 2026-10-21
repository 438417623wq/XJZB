import io
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\net\LanDiscovery.java"
src = io.open(p, encoding="utf-8").read()
# move the two trailing fields up with the rest, and drop the trailing underscores
src = src.replace('''    private DatagramSocket socket;
    private Thread listener;
    private volatile boolean running;
''', '''    private DatagramSocket socket;
    private Thread listener;
    private volatile boolean running;
    private Listener listener_;
    private String myVersion_ = "";
''')
src = src.replace('''
    private Listener listener_;
    private String myVersion_ = "";

    public void stop() {''', '''
    public void stop() {''')
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("reordered")