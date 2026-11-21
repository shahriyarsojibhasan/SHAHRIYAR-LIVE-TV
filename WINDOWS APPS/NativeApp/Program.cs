using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using Microsoft.Web.WebView2.WinForms;
using Microsoft.Web.WebView2.Core;

namespace ShahriyarLiveTV
{
    public class MainForm : Form
    {
        private WebView2 webView;
        private bool isFullScreen = false;
        private FormWindowState prevWindowState;
        private FormBorderStyle prevBorderStyle;

        public MainForm()
        {
            this.Text = "SHAHRIYAR LIVE TV";
            this.Size = new Size(1280, 750);
            this.MinimumSize = new Size(800, 500);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(11, 17, 33);
            
            // Set Application Icon
            string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "icon.ico");
            if (File.Exists(iconPath))
            {
                try { this.Icon = new Icon(iconPath); } catch { }
            }

            // Keyboard shortcut handling
            this.KeyPreview = true;
            this.KeyDown += MainForm_KeyDown;

            webView = new WebView2();
            webView.Dock = DockStyle.Fill;
            this.Controls.Add(webView);

            InitializeWebView();
        }

        private async void InitializeWebView()
        {
            try
            {
                string userDataFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SHAHRIYAR_LIVE_TV");
                var env = await CoreWebView2Environment.CreateAsync(null, userDataFolder);
                await webView.EnsureCoreWebView2Async(env);

                // Configure browser settings
                webView.CoreWebView2.Settings.IsStatusBarEnabled = false;
                webView.CoreWebView2.Settings.AreDevToolsEnabled = false;
                webView.CoreWebView2.Settings.IsZoomControlEnabled = false;

                // Handle Fullscreen elements from Plyr video player
                webView.CoreWebView2.ContainsFullScreenElementChanged += (s, e) =>
                {
                    SetFullScreen(webView.CoreWebView2.ContainsFullScreenElement);
                };

                // Navigate to local index.html if present, else fallback to live web app
                string localHtml = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "index.html");
                if (File.Exists(localHtml))
                {
                    webView.CoreWebView2.Navigate(new Uri(localHtml).AbsoluteUri);
                }
                else
                {
                    webView.CoreWebView2.Navigate("https://shahriyarsojibhasan.github.io/SHAHRIYAR-LIVE-TV/");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Unable to initialize WebView2:\n" + ex.Message + "\n\nPlease ensure Microsoft Edge WebView2 Runtime is installed.", "SHAHRIYAR LIVE TV", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        private void SetFullScreen(bool full)
        {
            if (full == isFullScreen) return;

            if (full)
            {
                prevWindowState = this.WindowState;
                prevBorderStyle = this.FormBorderStyle;
                this.FormBorderStyle = FormBorderStyle.None;
                this.WindowState = FormWindowState.Maximized;
                isFullScreen = true;
            }
            else
            {
                this.FormBorderStyle = prevBorderStyle;
                this.WindowState = prevWindowState;
                isFullScreen = false;
            }
        }

        private void MainForm_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.F11)
            {
                SetFullScreen(!isFullScreen);
                e.Handled = true;
            }
            else if (e.KeyCode == Keys.Escape && isFullScreen)
            {
                SetFullScreen(false);
                e.Handled = true;
            }
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
