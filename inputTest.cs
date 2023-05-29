using System;
using System.Windows.Forms;
using System.Drawing;

namespace PenData
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            // Create a new pen input device.
            var penDevice = new PenInputDevice();

            // Subscribe to the pen down event.
            penDevice.PenDown += new PenInputDeviceEventHandler(penDevice_PenDown);

            // Start the pen input device.
            penDevice.Start();
        }

        private void penDevice_PenDown(object sender, PenInputDeviceEventArgs e)
        {
            // Get the pen position.
            Point position = e.Position;

            // Draw a circle at the pen position.
            Graphics.FromHwnd(this.Handle).DrawCircle(Pens.Black, position, 10);
        }
    }
}