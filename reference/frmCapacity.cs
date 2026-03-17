// EvenMoreAwareDashboard, Version=1.1.0.0, Culture=neutral, PublicKeyToken=null
// EvenMoreAwareDashboard.frmCapacity
using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Printing;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Windows.Forms.DataVisualization.Charting;
using DataStreams.Csv;
using EvenMoreAware;
using EvenMoreAwareDashboard;
using EvenMoreAwareDashboard.Properties;
using EvenMoreAwareDashboard.ServiceReference1;
using Moraware.JobTrackerAPI5;

public class frmCapacity : Form
{
	private class CapacityForActivity
	{
		public string Activity_Type_Name { get; set; }

		public decimal qty { get; set; }

		public decimal value { get; set; }

		public int actCount { get; set; }

		public List<EvenMoreAwareDataSet.Capacity_VariableRow> capVarRows { get; set; }
	}

	public Form1 Form1 = null;

	public Connection MWConnect = null;

	private CookieAwareWebClient client = null;

	public EvenMoreAwareDataSet.Company_LocationRow compLocRow = null;

	private List<JobActivity> mwacts = new List<JobActivity>();

	private List<Job> mwjobs = new List<Job>();

	private List<JobForm> mwforms = new List<JobForm>();

	public List<JobActivityStatus> mwstatuses = new List<JobActivityStatus>();

	public List<JobActivityCustomFieldType> cfTypes = new List<JobActivityCustomFieldType>();

	public List<JobActivityType> actTypes = new List<JobActivityType>();

	private Thread t;

	private List<Thread> threads = new List<Thread>();

	private object lockObject = new object();

	public EvenMoreAwareDataSet.Capacity_LockDataTable dtCapacityLocks = null;

	private List<Image> _pagesSplit = new List<Image>();

	private int pageIndex = 0;

	private IContainer components = null;

	private GroupBox groupBox1;

	private Button btnPrintPreview;

	private Button btnPrint;

	private CheckBox chkShowCharts;

	private Button btnRunReport;

	private DateTimePicker dateTimePicker1;

	private Label label1;

	private Label label2;

	private DateTimePicker dateTimePicker2;

	private ComboBox cbCompanyLocation;

	private Label lblCompanyLocation;

	private TableLayoutPanel tableLayoutPanel1;

	private Label lblStatus;

	private GroupBox groupBox2;

	private ListBox lbActivityType;

	private Label label5;

	private Label label4;

	private Button btnClear;

	private ToolTip toolTip1;

	private Button btnClearAct;

	private Button btnManageCapacityVariables;

	private PrintDialog printDialog1;

	private CheckBox chkIgnoreCancelled;

	private CheckBox chkFilterActsWithVariables;

	public ListBox lbAssignee;

	private System.Windows.Forms.Timer timer1;

	private PictureBox pbHelp;

	private Button btnCapacityLocks;

	public frmCapacity()
	{
		InitializeComponent();
	}

	private void frmCapacity_Load(object sender, EventArgs e)
	{
		foreach (Form openForm in Application.OpenForms)
		{
			if (openForm.Name == "Form1")
			{
				Form1 = (Form1)openForm;
				break;
			}
		}
		if (Form1.dtCompany.Count > 0)
		{
			cbCompanyLocation.Enabled = Form1.dtCompanyLocations.Count > 1;
			switch (Form1.dtCompanyLocations.Count)
			{
			case 0:
				MessageBox.Show("There are no active company locations on your account!", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Hand);
				Close();
				return;
			case 1:
				compLocRow = Form1.dtCompanyLocations.First();
				if (!createConnections(compLocRow))
				{
					Close();
					return;
				}
				break;
			default:
			{
				cbCompanyLocation.SelectedIndexChanged -= cbCompanyLocation_SelectedIndexChanged;
				cbCompanyLocation.DataSource = Form1.dtCompanyLocations;
				cbCompanyLocation.DisplayMember = "Company_Location_Name";
				cbCompanyLocation.ValueMember = "Company_Location_Id";
				cbCompanyLocation.SelectedIndex = -1;
				cbCompanyLocation.SelectedIndexChanged += cbCompanyLocation_SelectedIndexChanged;
				int capacity_Last_Location_Id = Settings.Default.Capacity_Last_Location_Id;
				if (Settings.Default.Capacity_Last_Location_Id > -1)
				{
					cbCompanyLocation.SelectedValue = Settings.Default.Capacity_Last_Location_Id;
					if (cbCompanyLocation.SelectedValue == null)
					{
						cbCompanyLocation.SelectedIndex = 0;
					}
				}
				else
				{
					cbCompanyLocation.SelectedIndex = 0;
				}
				break;
			}
			}
			chkFilterActsWithVariables.CheckedChanged -= chkFilterActsWithVariables_CheckedChanged;
			chkFilterActsWithVariables.Checked = Settings.Default.Capacity_Filter_Acts_With_Variables;
			chkFilterActsWithVariables.CheckedChanged += chkFilterActsWithVariables_CheckedChanged;
			if (Form1.dtCapacityVariables != null)
			{
				lock (Form1.dtCapacityVariables)
				{
					Form1.dtCapacityVariables = Form1.serviceClient.getCapacityVariablesForCompanyId(Form1.dtCompany.First().Company_Id, Settings.Default.EvenMoreAwarePassword);
					if (Form1.dtCapacityVariables.Count == 0)
					{
						openCapacityVariables();
					}
				}
			}
			else
			{
				Form1.dtCapacityVariables = Form1.serviceClient.getCapacityVariablesForCompanyId(Form1.dtCompany.First().Company_Id, Settings.Default.EvenMoreAwarePassword);
				if (Form1.dtCapacityVariables.Count == 0)
				{
					openCapacityVariables();
				}
			}
			fillActivityTypesAndAssignees();
			dtCapacityLocks = Form1.serviceClient.GetCapacity_Locks(compLocRow.Company_Location_Id, Settings.Default.EvenMoreAwarePassword, DateTime.Now.AddDays(-30.0));
			updateLockBtnCount();
			timer1.Start();
		}
		else
		{
			MessageBox.Show("Your account is not validated to use this service.", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Hand);
			Close();
		}
	}

	private void openCapacityVariables()
	{
		frmCapacityVariables frmCapacityVariables2 = new frmCapacityVariables();
		frmCapacityVariables2.Owner = this;
		frmCapacityVariables2.ShowDialog();
		if (frmCapacityVariables2.changed)
		{
			MessageBox.Show("Capacity variables were updated successfully!  Run or refresh report.", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Asterisk);
		}
		frmCapacityVariables2.Dispose();
		getActTypes();
	}

	private void fillActivityTypesAndAssignees()
	{
		if (!MWConnect.Connected)
		{
			EvenMoreAwareDashboard.Security.setMWConnectSessionFromWS(MWConnect, Form1.serviceClient, compLocRow.Company_Id, compLocRow.Company_Location_Id);
			EvenMoreAwareDashboard.Security.setWebClientSessionFromConnection(MWConnect, client);
		}
		actTypes = (from at in MWConnect.GetJobActivityTypes(1)
			where !at.IsInactive
			orderby at.JobActivityTypeName
			select at).ToList();
		getActTypes();
		lbAssignee.DataSource = (from a in MWConnect.GetAssignees()
			where !a.IsInactive
			orderby a.AssigneeName
			select a).ToList();
		Demo.maskAssignees(lbAssignee.DataSource as List<Assignee>, compLocRow);
		cfTypes = (from at in MWConnect.GetCustomJobActivityFieldTypes(includeInactive_: false)
			orderby at.CustomFieldTypeName
			select at).ToList();
		mwstatuses = MWConnect.GetJobActivityStatuses();
		lbActivityType.DisplayMember = "JobActivityTypeName";
		lbActivityType.ValueMember = "JobActivityTypeId";
		lbActivityType.ClearSelected();
		lbAssignee.DisplayMember = "AssigneeName";
		lbAssignee.ValueMember = "AssigneeId";
		lbAssignee.ClearSelected();
	}

	private bool createConnections(EvenMoreAwareDataSet.Company_LocationRow compLocRow)
	{
		try
		{
			MWConnect = new Connection();
			MWConnect.Url = compLocRow.Company_Location_Moraware_Url.TrimEnd('/') + "/api.aspx";
			MWConnect.UserName = compLocRow.Company_Location_Moraware_Username;
			MWConnect.Password = EvenMoreAwareDashboard.Security.Decrypt(compLocRow.Company_Location_Moraware_Password, useHashing: true, Settings.Default.EvenMoreAwareCompanyKey);
			MWConnect.CompressRequests = true;
			MWConnect.CompressResponses = true;
			MWConnect.AutoRefreshOnTimeout = true;
			EvenMoreAwareDashboard.Security.setMWConnectSessionFromWS(MWConnect, Form1.serviceClient, compLocRow.Company_Id, compLocRow.Company_Location_Id);
			client = EvenMoreAware5.CreateClient(compLocRow.Company_Location_Moraware_Url, compLocRow.Company_Location_Moraware_Username, EvenMoreAwareDashboard.Security.Decrypt(compLocRow.Company_Location_Moraware_Password, useHashing: true, Settings.Default.EvenMoreAwareCompanyKey), MWConnect);
			return true;
		}
		catch (Exception)
		{
			MessageBox.Show("There may be missing or incorrect information in your EvenMoreAware account.  Please contact us!", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Hand);
			return false;
		}
	}

	private void cbCompanyLocation_SelectedIndexChanged(object sender, EventArgs e)
	{
		if (cbCompanyLocation.SelectedIndex > -1)
		{
			compLocRow = (EvenMoreAwareDataSet.Company_LocationRow)(cbCompanyLocation.SelectedItem as DataRowView).Row;
			if (!createConnections(compLocRow))
			{
				Close();
			}
			Settings.Default.Capacity_Last_Location_Id = (int)cbCompanyLocation.SelectedValue;
			Settings.Default.Save();
			fillActivityTypesAndAssignees();
		}
	}

	private void updateStatus(string status)
	{
		Invoke((MethodInvoker)delegate
		{
			lblStatus.Text = "Status: " + status;
			lblStatus.Update();
			Update();
		});
	}

	private void btnRunReport_Click(object sender, EventArgs e)
	{
		Invoke((MethodInvoker)delegate
		{
			btnRunReport.Enabled = false;
			btnRunReport.Update();
			Update();
		});
		if (dateTimePicker2.Value < dateTimePicker1.Value)
		{
			Invoke((MethodInvoker)delegate
			{
				btnRunReport.Enabled = true;
				btnRunReport.Update();
				Update();
			});
			MessageBox.Show("Please check your date range!", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
			return;
		}
		System.Windows.Forms.Cursor current = System.Windows.Forms.Cursor.Current;
		System.Windows.Forms.Cursor.Current = Cursors.WaitCursor;
		while (tableLayoutPanel1.Controls.Count > 0)
		{
			tableLayoutPanel1.Controls[0].Dispose();
		}
		tableLayoutPanel1.Controls.Clear();
		tableLayoutPanel1.RowCount = 0;
		mwacts.Clear();
		mwjobs.Clear();
		mwforms.Clear();
		buildReport();
		Invoke((MethodInvoker)delegate
		{
			btnRunReport.Enabled = true;
			btnRunReport.Update();
			Update();
		});
		System.Windows.Forms.Cursor.Current = current;
	}

	private void frmCapacity_FormClosing(object sender, FormClosingEventArgs e)
	{
		if (compLocRow == null)
		{
			return;
		}
		try
		{
			timer1.Stop();
			client.DownloadString(compLocRow["Company_Location_Moraware_Url"].ToString().TrimEnd('/') + "/d.aspx?LOGOUT=1");
			client.Dispose();
			if (MWConnect.Connected)
			{
				MWConnect.Disconnect();
			}
		}
		catch
		{
		}
	}

	private string buildURL()
	{
		DateTime dateTime = Convert.ToDateTime(dateTimePicker1.Value.ToShortDateString());
		DateTime dateTime2 = Convert.ToDateTime(dateTimePicker2.Value.ToShortDateString()).AddDays(1.0);
		int days = (dateTime2 - dateTime).Days;
		string text = compLocRow.Company_Location_Moraware_Url.TrimEnd('/') + "/d.aspx?wp=3&view=0";
		text = text + "&activityType=" + getActIds();
		if (lbAssignee.SelectedItems.Count > 0)
		{
			text = text + "&assigneeId=" + getAssIds();
		}
		text = text + "&effdate=" + dateTime.Year + "-" + dateTime.Month + "-" + dateTime.Day;
		if (days > 0)
		{
			text = text + "&dayCount=" + days;
		}
		return text + "&display=1";
	}

	private string getActIds()
	{
		string text = "";
		foreach (object selectedItem in lbActivityType.SelectedItems)
		{
			text = text + (selectedItem as JobActivityType).JobActivityTypeId + ",";
		}
		return text.TrimEnd(',');
	}

	private string getAssIds()
	{
		string text = "";
		foreach (object selectedItem in lbAssignee.SelectedItems)
		{
			text = text + (selectedItem as Assignee).AssigneeId + ",";
		}
		return text.TrimEnd(',');
	}

	private void btnClear_Click(object sender, EventArgs e)
	{
		lbAssignee.ClearSelected();
	}

	private void btnManageCapacityVariables_Click(object sender, EventArgs e)
	{
		openCapacityVariables();
	}

	private void buildReport()
	{
		if (!MWConnect.Connected)
		{
			EvenMoreAwareDashboard.Security.setMWConnectSessionFromWS(MWConnect, Form1.serviceClient, compLocRow.Company_Id, compLocRow.Company_Location_Id);
			EvenMoreAwareDashboard.Security.setWebClientSessionFromConnection(MWConnect, client);
		}
		if (cbCompanyLocation.Enabled && cbCompanyLocation.SelectedIndex == -1)
		{
			MessageBox.Show("Please choose a company location!", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Hand);
			return;
		}
		if (lbActivityType.SelectedItems.Count == 0)
		{
			MessageBox.Show("Please choose at least 1 activity type!", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Hand);
			return;
		}
		foreach (object i in lbActivityType.SelectedItems)
		{
			lock (Form1.dtCapacityVariables)
			{
				if (Form1.dtCapacityVariables.Where((EvenMoreAwareDataSet.Capacity_VariableRow cv) => cv.Activity_Type_Id == (i as JobActivityType).JobActivityTypeId).FirstOrDefault() == null)
				{
					MessageBox.Show("Please check that there are capacity variables for selected activity type(s)!", "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Hand);
					return;
				}
			}
		}
		updateStatus("Getting latest capacity locks...");
		dtCapacityLocks = Form1.serviceClient.GetCapacity_Locks(compLocRow.Company_Location_Id, Settings.Default.EvenMoreAwarePassword, DateTime.Now.AddDays(-30.0));
		updateLockBtnCount();
		updateStatus("Getting activity ids...");
		string url = buildURL();
		List<int> jobActivityIdsFromCalendarViewUrl = EvenMoreAware5.GetJobActivityIdsFromCalendarViewUrl(client, url, Pages: false);
		if (jobActivityIdsFromCalendarViewUrl.Count == 0)
		{
			try
			{
				List<JTProcess> processes = MWConnect.GetProcesses();
			}
			catch
			{
				EvenMoreAwareDashboard.Security.setMWConnectSessionFromWS(MWConnect, Form1.serviceClient, compLocRow.Company_Id, compLocRow.Company_Location_Id);
				EvenMoreAwareDashboard.Security.setWebClientSessionFromConnection(MWConnect, client);
			}
		}
		updateStatus("Getting job activites from Moraware...");
		try
		{
			if (jobActivityIdsFromCalendarViewUrl.Count > 0)
			{
				threads.Clear();
				int num = 1;
				int num2 = 0;
				foreach (int item in jobActivityIdsFromCalendarViewUrl)
				{
					t = new Thread(getAct);
					threads.Add(t);
					t.Start(item);
					num++;
					if (num2 == 25)
					{
						while (threads.Where((Thread t) => t.IsAlive).FirstOrDefault() != null)
						{
						}
						num2 = 0;
					}
					num2++;
				}
				do
				{
					updateStatus("Getting job activites from Moraware [" + mwacts.Count + " of " + jobActivityIdsFromCalendarViewUrl.Count + "]...");
				}
				while (threads.Where((Thread t) => t.IsAlive).FirstOrDefault() != null);
				updateStatus("Getting " + mwacts.Select((JobActivity a) => a.JobId).Distinct().Count() + " jobs and job forms from Moraware...");
				Thread thread = new Thread(getJobs);
				thread.Start();
				lock (Form1.dtCapacityVariables)
				{
					if (Form1.dtCapacityVariables.Where((EvenMoreAwareDataSet.Capacity_VariableRow cv) => !cv.IsCapacity_Variable_Fallback_Form_Template_IdNull()).FirstOrDefault() != null)
					{
						threads.Clear();
						num2 = 0;
						foreach (int item2 in mwacts.Select((JobActivity a) => a.JobId).Distinct())
						{
							t = new Thread(getForms);
							threads.Add(t);
							t.Start(item2);
							if (num2 == 10)
							{
								while (threads.Where((Thread t) => t.IsAlive).FirstOrDefault() != null)
								{
								}
								num2 = 0;
							}
							num2++;
						}
						while (threads.Where((Thread t) => t.IsAlive).FirstOrDefault() != null)
						{
						}
					}
				}
				while (thread.IsAlive)
				{
				}
			}
		}
		catch
		{
		}
		try
		{
			foreach (object selectedItem in lbActivityType.SelectedItems)
			{
				updateStatus("Creating " + (selectedItem as JobActivityType).JobActivityTypeName + " capacity report...");
				createGrid(selectedItem as JobActivityType);
			}
		}
		catch (Exception ex)
		{
			MessageBox.Show("There was an error building report.  Please try again. " + ex.ToString(), "EvenMoreAware", MessageBoxButtons.OK, MessageBoxIcon.Hand);
		}
		updateStatus("Idle...");
	}

	private void getJobs()
	{
		mwjobs = MWConnect.GetJobs(mwacts.Select((JobActivity a) => a.JobId).Distinct());
	}

	private void getForms(object id)
	{
		List<JobForm> jobForms = MWConnect.GetJobForms((int)id, includeJobPhases_: true, Connection.GetJobForm_FieldInclusionType_Enum.AllFields);
		if (jobForms != null && jobForms.Count > 0)
		{
			lock (lockObject)
			{
				mwforms.AddRange(jobForms);
			}
		}
	}

	private void getAct(object id)
	{
		JobActivity jobActivity = MWConnect.GetJobActivity((int)id, includeJobPhases_: true, includeJobActivitySeriesMember_: false);
		lock (lockObject)
		{
			mwacts.Add(jobActivity);
		}
	}

	private void createGrid(JobActivityType actType)
	{
		List<EvenMoreAwareDataSet.Capacity_VariableRow> list = new List<EvenMoreAwareDataSet.Capacity_VariableRow>();
		lock (Form1.dtCapacityVariables)
		{
			list = (from cv in Form1.dtCapacityVariables
				where cv.Activity_Type_Id == actType.JobActivityTypeId
				orderby cv.Column_Order
				select cv).ToList();
		}
		List<JobActivity> list2 = new List<JobActivity>();
		list2 = ((!chkIgnoreCancelled.Checked) ? mwacts.Where((JobActivity a) => a.JobActivityTypeId == actType.JobActivityTypeId).ToList() : mwacts.Where((JobActivity a) => a.JobActivityTypeId == actType.JobActivityTypeId && mwstatuses.Where((JobActivityStatus s) => s.JobActivityStatusId == a.JobActivityStatusId).First().JobActivityStatusType != JobActivityStatus.JobActivityStatusType_Enum.Canceled).ToList());
		if (list2.Count() <= 0)
		{
			return;
		}
		int count = tableLayoutPanel1.Controls.Count;
		DataTable dataTable = buildTblCap(list, list2);
		Label label = new Label();
		label.AutoSize = true;
		string text = "";
		foreach (EvenMoreAwareDataSet.Capacity_VariableRow item2 in list)
		{
			text = text + item2.Capacity_Variable_Name + ", ";
		}
		label.Text = "Capacity: " + text.Trim().TrimEnd(',');
		if (lbAssignee.SelectedItems.Count > 0)
		{
			label.TextAlign = ContentAlignment.MiddleCenter;
			label.Text += Environment.NewLine;
			string text2 = "";
			foreach (object selectedItem in lbAssignee.SelectedItems)
			{
				text2 = text2 + (selectedItem as Assignee).AssigneeName + Environment.NewLine;
			}
			label.Text += text2;
		}
		tableLayoutPanel1.Controls.Add(label, 0, count);
		label.Anchor = AnchorStyles.Top;
		DataGridView dataGridView = new DataGridView();
		tableLayoutPanel1.Controls.Add(dataGridView, 0, count + 1);
		dataGridView.DataSource = dataTable;
		setupDataGrid(dataGridView, list);
		Button button = new Button();
		button.Text = label.Text + " Detail";
		button.Cursor = Cursors.Hand;
		button.Width = 300;
		button.BackColor = Color.LightSteelBlue;
		button.FlatStyle = FlatStyle.Flat;
		tableLayoutPanel1.Controls.Add(button, 0, count + 2);
		button.Anchor = AnchorStyles.Top;
		button.Tag = new object[5] { list2, mwjobs, list, mwforms, button.Text };
		button.Click += detailButtonClick;
		Button button2 = new Button();
		button2.Text = "";
		button2.BackColor = Color.LightSteelBlue;
		button2.Image = Resources.excel_17x17;
		button2.Width = 25;
		button2.Cursor = Cursors.Hand;
		button2.FlatStyle = FlatStyle.Flat;
		tableLayoutPanel1.Controls.Add(button2, 0, count + 2);
		button2.Anchor = AnchorStyles.Top;
		button2.Tag = dataTable;
		button2.Click += exportButtonClick;
		int jobCount = list2.Select((JobActivity a) => a.JobId).Distinct().Count();
		int count2 = list2.Count;
		DataGridView dataGridView2 = boxScoreDGV(dataTable, list, text, jobCount, count2);
		tableLayoutPanel1.Controls.Add(dataGridView2, 0, count + 3);
		dataGridView2.ClearSelection();
		dataGridView2.Columns[0].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
		dataGridView2.Columns[1].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
		if (dataGridView2.Columns.Count > 2)
		{
			dataGridView2.Columns[2].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
		}
		dataGridView2.Height = dgvHeight(dataGridView2);
		if (chkShowCharts.Checked && dataTable.Rows.Count > 0)
		{
			foreach (EvenMoreAwareDataSet.Capacity_VariableRow cvRow in list.OrderByDescending((EvenMoreAwareDataSet.Capacity_VariableRow cv) => cv.Column_Order))
			{
				Chart chart = new Chart();
				Series item = new Series();
				ChartArea chartArea = new ChartArea();
				Title title = new Title();
				chartArea.Name = "ChartArea";
				title.Name = "Chart";
				chart.Titles.Add(title);
				chart.ChartAreas.Add(chartArea);
				chartArea.AxisY.LabelAutoFitStyle = LabelAutoFitStyles.None;
				chartArea.AxisY.LabelStyle.Font = new Font("Arial", 8f, FontStyle.Regular);
				chartArea.AxisX.LabelAutoFitStyle = LabelAutoFitStyles.None;
				chartArea.AxisX.LabelStyle.Font = new Font("Arial", 8f, FontStyle.Regular);
				chartArea.AxisX.LabelStyle.Format = "MM/dd";
				chartArea.AxisX.LabelStyle.Angle = 45;
				chart.Series.Add(item);
				chart.Series[0]["PixelPointWidth"] = "15";
				string text3 = "";
				text3 = (cvRow.IsCapacity_Variable_Custom_Field_Type_IdNull() ? cvRow.Capacity_Variable_Name : cfTypes.Where((JobActivityCustomFieldType cf) => cf.CustomFieldTypeId == cvRow.Capacity_Variable_Custom_Field_Type_Id).First().CustomFieldTypeName);
				chart.Series[0].Points.DataBindXY(dataTable.Rows, "Act_Date", dataTable.Rows, text3);
				tableLayoutPanel1.Controls.Add(chart, 0, count + 4);
				chartArea.AxisX.Interval = 1.0;
				chart.Width = tableLayoutPanel1.Width - 10;
				chart.Height = 200;
				chart.Anchor = AnchorStyles.Top;
			}
		}
		Panel panel = new Panel();
		panel.Width = tableLayoutPanel1.Width - 50;
		panel.Height = 3;
		panel.BackColor = Color.Black;
		panel.BorderStyle = BorderStyle.None;
		if (chkShowCharts.Checked)
		{
			tableLayoutPanel1.Controls.Add(panel, 0, count + 5);
		}
		else
		{
			tableLayoutPanel1.Controls.Add(panel, 0, count + 4);
		}
		panel.Anchor = AnchorStyles.Top;
		count = tableLayoutPanel1.Controls.Count;
	}

	private DataGridView boxScoreDGV(DataTable tblCapacity, List<EvenMoreAwareDataSet.Capacity_VariableRow> cvRows, string type, int jobCount, int actCount)
	{
		DataGridView dataGridView = new DataGridView();
		dataGridView.AllowUserToAddRows = false;
		dataGridView.Enabled = false;
		dataGridView.Anchor = AnchorStyles.Top;
		dataGridView.Width = 600;
		dataGridView.BackgroundColor = Color.White;
		dataGridView.ColumnHeadersDefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
		dataGridView.ColumnHeadersDefaultCellStyle.BackColor = Color.SteelBlue;
		dataGridView.ColumnHeadersDefaultCellStyle.ForeColor = Color.White;
		dataGridView.AllowUserToAddRows = false;
		dataGridView.RowHeadersVisible = false;
		dataGridView.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
		dataGridView.EnableHeadersVisualStyles = false;
		dataGridView.ReadOnly = true;
		DataTable dataTable = new DataTable();
		DataColumn column = new DataColumn(" ");
		DataColumn column2 = new DataColumn(cvRows.First().Capacity_Variable_Name);
		dataTable.Columns.Add(column);
		dataTable.Columns.Add(column2);
		bool flag = cvRows.Count == 2;
		if (flag)
		{
			DataColumn column3 = new DataColumn(cvRows.Last().Capacity_Variable_Name);
			dataTable.Columns.Add(column3);
		}
		decimal num = default(decimal);
		decimal num2 = default(decimal);
		decimal num3 = default(decimal);
		decimal d = default(decimal);
		decimal d2 = default(decimal);
		decimal num4 = default(decimal);
		decimal num5 = default(decimal);
		num4 = ((!cvRows.First().IsCapacity_Variable_Is_MoneyNull() && cvRows.First().Capacity_Variable_Is_Money) ? cvRows.First().Capacity_Variable_Max_Money : ((decimal)cvRows.First().Capacity_Variable_Max_Int));
		if (flag)
		{
			num5 = ((!cvRows.Last().IsCapacity_Variable_Is_MoneyNull() && cvRows.Last().Capacity_Variable_Is_Money) ? cvRows.Last().Capacity_Variable_Max_Money : ((decimal)cvRows.Last().Capacity_Variable_Max_Int));
		}
		foreach (DataRow row in tblCapacity.Rows)
		{
			try
			{
				num += Convert.ToDecimal(row[1]);
			}
			catch
			{
			}
			++num3;
			d = num / num3;
			if (flag)
			{
				num2 += Convert.ToDecimal(row[3]);
				d2 = num2 / num3;
			}
		}
		DataRow dataRow2 = dataTable.NewRow();
		dataRow2[" "] = "Report Total:";
		if (num3 > 0m)
		{
			string text = Math.Round(num, 2).ToString();
			if (!cvRows.First().IsCapacity_Variable_Is_MoneyNull() && cvRows.First().Capacity_Variable_Is_Money)
			{
				text = Math.Round(num, 2).ToString("C");
			}
			dataRow2[cvRows.First().Capacity_Variable_Name] = text + " / " + Math.Round(num / (num4 * num3) * 100m, 2) + "%";
			if (flag)
			{
				string text2 = Math.Round(num2, 2).ToString();
				if (!cvRows.Last().IsCapacity_Variable_Is_MoneyNull() && cvRows.Last().Capacity_Variable_Is_Money)
				{
					text2 = Math.Round(num2, 2).ToString("C");
				}
				dataRow2[cvRows.Last().Capacity_Variable_Name] = text2 + " / " + Math.Round(num2 / (num5 * num3) * 100m, 2) + "%";
			}
		}
		else
		{
			dataRow2[cvRows.First().Capacity_Variable_Name] = "0%";
			if (flag)
			{
				dataRow2[cvRows.Last().Capacity_Variable_Name] = "0%";
			}
		}
		DataRow dataRow3 = dataTable.NewRow();
		dataRow3[" "] = "# Bus Days / Job Count / Act Count:";
		dataRow3[cvRows.First().Capacity_Variable_Name] = num3 + "/" + jobCount + "/" + actCount;
		if (flag)
		{
			dataRow3[cvRows.Last().Capacity_Variable_Name] = num3 + "/" + jobCount + "/" + actCount;
		}
		DataRow dataRow4 = dataTable.NewRow();
		dataRow4[" "] = "Daily Avg:";
		string value = Math.Round(d, 2).ToString();
		if (!cvRows.First().IsCapacity_Variable_Is_MoneyNull() && cvRows.First().Capacity_Variable_Is_Money)
		{
			value = Math.Round(d, 2).ToString("C");
		}
		dataRow4[cvRows.First().Capacity_Variable_Name] = value;
		if (flag)
		{
			string value2 = Math.Round(d2, 2).ToString();
			if (!cvRows.Last().IsCapacity_Variable_Is_MoneyNull() && cvRows.Last().Capacity_Variable_Is_Money)
			{
				value2 = Math.Round(d2, 2).ToString("C");
			}
			dataRow4[cvRows.Last().Capacity_Variable_Name] = value2;
		}
		DataRow dataRow5 = null;
		if (flag)
		{
			dataRow5 = dataTable.NewRow();
			dataRow5[" "] = "Average Value/Unit Of Measure:";
			if (!cvRows.Last().IsCapacity_Variable_Is_MoneyNull() && cvRows.Last().Capacity_Variable_Is_Money)
			{
				if (num == 0m)
				{
					num = 1m;
				}
				if (!cvRows.First().IsCapacity_Variable_Custom_Field_Type_IdNull())
				{
					dataRow5[cvRows.First().Capacity_Variable_Name] = (num2 / num).ToString("C") + "/" + cfTypes.Where((JobActivityCustomFieldType cft) => cft.CustomFieldTypeId == cvRows.First().Capacity_Variable_Custom_Field_Type_Id).First().CustomFieldTypeName;
				}
				else
				{
					dataRow5[cvRows.First().Capacity_Variable_Name] = (num2 / num).ToString("C") + "/" + cvRows.First().Capacity_Variable_Name;
				}
			}
			else
			{
				if (num2 == 0m)
				{
					num2 = 1m;
				}
				if (!cvRows.First().IsCapacity_Variable_Custom_Field_Type_IdNull())
				{
					dataRow5[cvRows.First().Capacity_Variable_Name] = (num / num2).ToString("C") + "/" + cfTypes.Where((JobActivityCustomFieldType cft) => cft.CustomFieldTypeId == cvRows.Last().Capacity_Variable_Custom_Field_Type_Id).First().CustomFieldTypeName;
				}
				else
				{
					dataRow5[cvRows.First().Capacity_Variable_Name] = (num / num2).ToString("C") + "/" + cvRows.First().Capacity_Variable_Name;
				}
			}
		}
		dataTable.Rows.Add(dataRow2);
		dataTable.Rows.Add(dataRow3);
		dataTable.Rows.Add(dataRow4);
		if (flag && dataRow5 != null)
		{
			dataTable.Rows.Add(dataRow5);
		}
		dataGridView.DataSource = dataTable;
		return dataGridView;
	}

	private DataTable buildTblCap(List<EvenMoreAwareDataSet.Capacity_VariableRow> cvRows, List<JobActivity> gridMWActs)
	{
		DataTable dataTable = new DataTable();
		DataColumn column = new DataColumn("Act_Date", typeof(string));
		dataTable.Columns.Add(column);
		foreach (EvenMoreAwareDataSet.Capacity_VariableRow cvRow in cvRows)
		{
			if (!cvRow.IsCapacity_Variable_Custom_Field_Type_IdNull())
			{
				DataColumn column2 = new DataColumn(cfTypes.Where((JobActivityCustomFieldType cf) => cf.CustomFieldTypeId == cvRow.Capacity_Variable_Custom_Field_Type_Id).First().CustomFieldTypeName, typeof(decimal));
				dataTable.Columns.Add(column2);
				DataColumn column3 = new DataColumn(cfTypes.Where((JobActivityCustomFieldType cf) => cf.CustomFieldTypeId == cvRow.Capacity_Variable_Custom_Field_Type_Id).First().CustomFieldTypeName + "_Util", typeof(decimal));
				dataTable.Columns.Add(column3);
			}
			else
			{
				DataColumn column4 = new DataColumn(cvRow.Capacity_Variable_Name, typeof(decimal));
				dataTable.Columns.Add(column4);
				DataColumn column5 = new DataColumn(cvRow.Capacity_Variable_Name + "_Util", typeof(decimal));
				dataTable.Columns.Add(column5);
			}
		}
		List<DateTime?> list = (from d in gridMWActs.Select((JobActivity a) => a.StartDate).Distinct()
			orderby d.Value
			select d).ToList();
		foreach (DateTime? date in list)
		{
			DataRow dataRow = dataTable.NewRow();
			dataRow[0] = Convert.ToDateTime(date).ToShortDateString() + " - " + Convert.ToDateTime(date).DayOfWeek.ToString().Substring(0, 3);
			int num = 1;
			foreach (EvenMoreAwareDataSet.Capacity_VariableRow cvRow2 in cvRows)
			{
				IEnumerable<JobActivity> enumerable = gridMWActs.Where((JobActivity a) => a.JobActivityTypeId == cvRow2.Activity_Type_Id && a.StartDate == date);
				decimal v = default(decimal);
				foreach (JobActivity mwact in enumerable)
				{
					CustomFieldValue customFieldValue = mwact.CustomFieldValues.Where((CustomFieldValue cfv) => cfv.CustomFieldTypeId == cvRow2.Capacity_Variable_Custom_Field_Type_Id).FirstOrDefault();
					decimal result = default(decimal);
					if (customFieldValue != null && decimal.TryParse(customFieldValue.FieldValue, out result))
					{
						v += Convert.ToDecimal(customFieldValue.FieldValue);
					}
					else
					{
						if (cvRow2.IsCapacity_Variable_Fallback_Form_Template_IdNull() || cvRow2.IsCapacity_Variable_Fallback_Job_Form_Field_IdNull())
						{
							continue;
						}
						IEnumerable<JobForm> enumerable2 = mwforms.Where((JobForm f) => f != null && f.JobId == mwact.JobId && f.FormTemplateId == cvRow2.Capacity_Variable_Fallback_Form_Template_Id && PhaseRelated.isPhaseRelatedActForm(mwact, f));
						foreach (JobForm item in enumerable2)
						{
							if (item != null)
							{
								JobFormFieldValue jobFormFieldValue = item.FieldValues.Where((JobFormFieldValue fv) => fv.JobFormFieldId == cvRow2.Capacity_Variable_Fallback_Job_Form_Field_Id).FirstOrDefault();
								if (jobFormFieldValue != null && jobFormFieldValue.FieldValue != null && jobFormFieldValue.FieldValue != "" && (jobFormFieldValue.FormFieldDataType == FormTemplateField.FormFieldDataType_Enum.Number || jobFormFieldValue.FormFieldDataType == FormTemplateField.FormFieldDataType_Enum.Currency || jobFormFieldValue.FormFieldDataType == FormTemplateField.FormFieldDataType_Enum.Text))
								{
									v += Convert.ToDecimal(jobFormFieldValue.FieldValue);
								}
							}
						}
					}
				}
				v = Demo.maskDecimal(v, compLocRow);
				dataRow[num] = v;
				num++;
				if (cvRow2.IsCapacity_Variable_Is_MoneyNull() || !cvRow2.Capacity_Variable_Is_Money)
				{
					dataRow[num] = v / (decimal)cvRow2.Capacity_Variable_Max_Int * 100m;
				}
				else
				{
					dataRow[num] = v / cvRow2.Capacity_Variable_Max_Money * 100m;
				}
				num++;
			}
			dataRow.EndEdit();
			dataTable.Rows.Add(dataRow);
		}
		return dataTable;
	}

	private void setupDataGrid(DataGridView dgv, List<EvenMoreAwareDataSet.Capacity_VariableRow> cvRows)
	{
		dgv.Anchor = AnchorStyles.Top;
		dgv.Width = tableLayoutPanel1.Width - 50;
		dgv.BackgroundColor = Color.White;
		dgv.ColumnHeadersDefaultCellStyle.BackColor = Color.SteelBlue;
		dgv.ColumnHeadersDefaultCellStyle.ForeColor = Color.White;
		dgv.AlternatingRowsDefaultCellStyle.BackColor = Color.Gainsboro;
		dgv.AllowUserToAddRows = false;
		dgv.AllowUserToDeleteRows = false;
		dgv.AllowUserToResizeColumns = false;
		dgv.AllowUserToResizeRows = false;
		dgv.RowHeadersWidthSizeMode = DataGridViewRowHeadersWidthSizeMode.DisableResizing;
		dgv.RowHeadersVisible = false;
		dgv.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
		dgv.EnableHeadersVisualStyles = false;
		dgv.ReadOnly = true;
		dgv.ColumnHeadersDefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
		dgv.Columns[1].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
		if (cvRows[0].IsCapacity_Variable_Is_MoneyNull() || !cvRows[0].Capacity_Variable_Is_Money)
		{
			dgv.Columns[1].DefaultCellStyle.Format = "N2";
		}
		else
		{
			dgv.Columns[1].DefaultCellStyle.Format = "C";
		}
		dgv.Columns[2].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
		dgv.Columns[2].DefaultCellStyle.Format = "0\\%";
		if (dgv.Columns.Count > 3)
		{
			dgv.Columns[3].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
			if (cvRows[1].IsCapacity_Variable_Is_MoneyNull() || !cvRows[1].Capacity_Variable_Is_Money)
			{
				dgv.Columns[3].DefaultCellStyle.Format = "N2";
			}
			else
			{
				dgv.Columns[3].DefaultCellStyle.Format = "C";
			}
		}
		if (dgv.Columns.Count > 4)
		{
			dgv.Columns[4].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
			dgv.Columns[4].DefaultCellStyle.Format = "0\\%";
		}
		if (dtCapacityLocks != null)
		{
			EnumerableRowCollection<EvenMoreAwareDataSet.Capacity_LockRow> source = dtCapacityLocks.Where((EvenMoreAwareDataSet.Capacity_LockRow l) => l.Activity_Type_Id == cvRows[0].Activity_Type_Id && l.Capacity_Lock_Date >= Convert.ToDateTime(dateTimePicker1.Value.ToShortDateString()) && l.Capacity_Lock_Date <= Convert.ToDateTime(dateTimePicker2.Value.ToShortDateString()).AddDays(1.0));
			if (source.Count() > 0)
			{
				DataGridViewImageColumn dataGridViewImageColumn = new DataGridViewImageColumn();
				dataGridViewImageColumn.Name = "lockCol";
				dataGridViewImageColumn.ReadOnly = true;
				dataGridViewImageColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.DisplayedCells;
				dataGridViewImageColumn.HeaderText = "L";
				dgv.CellMouseEnter += gridView_CellMouseEnter;
				dgv.Columns.Add(dataGridViewImageColumn);
				foreach (DataGridViewRow item in (IEnumerable)dgv.Rows)
				{
					DateTime d1 = Convert.ToDateTime(Convert.ToDateTime(item.Cells[0].Value.ToString().Split('-')[0].Trim()).ToShortDateString());
					EvenMoreAwareDataSet.Capacity_LockRow capacity_LockRow = source.Where((EvenMoreAwareDataSet.Capacity_LockRow l) => Convert.ToDateTime(l.Capacity_Lock_Date.ToShortDateString()) == d1).FirstOrDefault();
					DataGridViewImageCell dataGridViewImageCell = (DataGridViewImageCell)item.Cells["lockCol"];
					object value;
					if (capacity_LockRow == null)
					{
						object obj = (dataGridViewImageCell.Style.NullValue = null);
						value = obj;
					}
					else
					{
						value = Resources.padlock;
					}
					dataGridViewImageCell.Value = value;
					dataGridViewImageCell.OwningRow.Cells["lockCol"].ToolTipText = ((capacity_LockRow != null) ? capacity_LockRow.Capacity_Lock_Reason : "");
					if (capacity_LockRow == null)
					{
						continue;
					}
					foreach (DataGridViewCell cell in item.Cells)
					{
						if (cell.OwningColumn.Name != "lockCol")
						{
							cell.Style.BackColor = Color.Yellow;
						}
					}
				}
			}
			dgv.AutoResizeRows();
		}
		dgv.Height = dgvHeight(dgv);
		dgv.ClearSelection();
		ModControls.disableSorting(dgv);
	}

	private void gridView_CellMouseEnter(object sender, DataGridViewCellEventArgs e)
	{
		if (!((sender as DataGridView).CurrentCell.OwningColumn.Name == "lockCol"))
		{
		}
	}

	private int dgvHeight(DataGridView dgv)
	{
		int num = dgv.ColumnHeadersHeight;
		foreach (DataGridViewRow item in (IEnumerable)dgv.Rows)
		{
			num += item.Height;
		}
		return num + 2;
	}

	private void detailButtonClick(object sender, EventArgs e)
	{
		frmCapacityReportDetail frmCapacityReportDetail2 = new frmCapacityReportDetail();
		frmCapacityReportDetail2.btnTag = (sender as Button).Tag as object[];
		frmCapacityReportDetail2.Owner = this;
		frmCapacityReportDetail2.Text = "EvenMoreAware - " + ((sender as Button).Tag as object[])[4];
		frmCapacityReportDetail2.Show();
	}

	private void exportButtonClick(object sender, EventArgs e)
	{
		SaveFileDialog saveFileDialog = new SaveFileDialog();
		saveFileDialog.Filter = "CSV|*.csv";
		saveFileDialog.Title = "Save CSV File";
		saveFileDialog.FileName = "CapacityGrid.csv";
		if (saveFileDialog.ShowDialog() == DialogResult.OK && saveFileDialog.FileName != "")
		{
			using (CsvWriter csvWriter = new CsvWriter(saveFileDialog.FileName, ',', Encoding.Default))
			{
				csvWriter.WriteAll((sender as Button).Tag as DataTable, writeHeaders: true);
			}
			Process.Start(saveFileDialog.FileName);
		}
	}

	private void btnClearAct_Click(object sender, EventArgs e)
	{
		lbActivityType.ClearSelected();
	}

	private void Doc_PrintPage(object sender, PrintPageEventArgs e)
	{
		e.Graphics.DrawImage(_pagesSplit[pageIndex], e.PageBounds.X, e.PageBounds.Y);
		pageIndex++;
		e.HasMorePages = pageIndex < _pagesSplit.Count;
	}

	private void splitPrint(Bitmap bmp, PrintDocument doc)
	{
		int num = 0;
		do
		{
			try
			{
				Rectangle rect = new Rectangle(0, num, bmp.Width, doc.DefaultPageSettings.PaperSize.Height - 100);
				int num2 = 0;
				for (int i = 0; i < tableLayoutPanel1.Controls.Count; i++)
				{
					Control control = tableLayoutPanel1.Controls[i];
					if (control.Visible && control.Top > rect.Top && control.Bottom > rect.Bottom && control.Height <= doc.DefaultPageSettings.PaperSize.Height - 100)
					{
						do
						{
							rect.Height--;
						}
						while (rect.Bottom > control.Top);
						num2 = i;
						break;
					}
				}
				if (num2 > 0 && tableLayoutPanel1.Controls[num2 - 1] is Label)
				{
					do
					{
						rect.Height--;
					}
					while (rect.Bottom > tableLayoutPanel1.Controls[num2 - 1].Top);
				}
				Bitmap item = bmp.Clone(rect, bmp.PixelFormat);
				_pagesSplit.Add(item);
				num += rect.Height;
			}
			catch
			{
				Rectangle rect2 = new Rectangle(0, num, bmp.Width, bmp.Height - num);
				Bitmap item2 = bmp.Clone(rect2, bmp.PixelFormat);
				_pagesSplit.Add(item2);
				break;
			}
		}
		while (num < bmp.Height);
	}

	private void btnPrintPreview_Click(object sender, EventArgs e)
	{
		if (tableLayoutPanel1.Controls.Count == 0)
		{
			return;
		}
		int num = tableLayoutPanel1.Width;
		int num2 = tableLayoutPanel1.Height;
		foreach (Control control3 in tableLayoutPanel1.Controls)
		{
			if (control3 is Button)
			{
				control3.Visible = false;
			}
		}
		tableLayoutPanel1.AutoScroll = false;
		tableLayoutPanel1.AutoSize = true;
		tableLayoutPanel1.Refresh();
		Bitmap bitmap = new Bitmap(tableLayoutPanel1.Width, tableLayoutPanel1.Height);
		tableLayoutPanel1.DrawToBitmap(bitmap, new Rectangle(0, 0, tableLayoutPanel1.Width, tableLayoutPanel1.Height));
		PrintDocument printDocument = new PrintDocument();
		printDocument.PrintPage += Doc_PrintPage;
		pageIndex = 0;
		IEnumerable<PaperSize> source = printDocument.PrinterSettings.PaperSizes.Cast<PaperSize>();
		printDocument.OriginAtMargins = true;
		printDocument.DefaultPageSettings.PaperSize = source.Where((PaperSize ps) => ps.Kind == PaperKind.Letter).First();
		System.Drawing.Printing.Margins margins = new System.Drawing.Printing.Margins(30, 30, 30, 30);
		printDocument.DefaultPageSettings.Margins = margins;
		splitPrint(bitmap, printDocument);
		PrintPreviewDialog printPreviewDialog = new PrintPreviewDialog();
		printPreviewDialog.Document = printDocument;
		printPreviewDialog.ShowDialog();
		printDocument.PrintPage -= Doc_PrintPage;
		if (_pagesSplit.Count > 0)
		{
			do
			{
				_pagesSplit[0].Dispose();
				_pagesSplit.RemoveAt(0);
			}
			while (_pagesSplit.Count > 0);
		}
		bitmap.Dispose();
		tableLayoutPanel1.AutoSize = false;
		tableLayoutPanel1.AutoScroll = true;
		tableLayoutPanel1.Width = num;
		tableLayoutPanel1.Height = num2;
		foreach (Control control4 in tableLayoutPanel1.Controls)
		{
			if (control4 is Button)
			{
				control4.Visible = true;
			}
		}
	}

	private void btnPrint_Click(object sender, EventArgs e)
	{
		if (tableLayoutPanel1.Controls.Count == 0)
		{
			return;
		}
		int num = tableLayoutPanel1.Width;
		int num2 = tableLayoutPanel1.Height;
		foreach (Control control3 in tableLayoutPanel1.Controls)
		{
			if (control3 is Button)
			{
				control3.Visible = false;
			}
		}
		tableLayoutPanel1.AutoScroll = false;
		tableLayoutPanel1.AutoSize = true;
		tableLayoutPanel1.Refresh();
		Bitmap bitmap = new Bitmap(tableLayoutPanel1.Width, tableLayoutPanel1.Height);
		tableLayoutPanel1.DrawToBitmap(bitmap, new Rectangle(0, 0, tableLayoutPanel1.Width, tableLayoutPanel1.Height));
		PrintDocument printDocument = new PrintDocument();
		printDocument.PrintPage += Doc_PrintPage;
		pageIndex = 0;
		IEnumerable<PaperSize> source = printDocument.PrinterSettings.PaperSizes.Cast<PaperSize>();
		printDocument.OriginAtMargins = true;
		printDocument.DefaultPageSettings.PaperSize = source.Where((PaperSize ps) => ps.Kind == PaperKind.Letter).First();
		System.Drawing.Printing.Margins margins = new System.Drawing.Printing.Margins(30, 30, 30, 30);
		printDocument.DefaultPageSettings.Margins = margins;
		splitPrint(bitmap, printDocument);
		printDialog1.Document = printDocument;
		if (printDialog1.ShowDialog() == DialogResult.OK)
		{
			printDocument.Print();
		}
		printDocument.PrintPage -= Doc_PrintPage;
		if (_pagesSplit.Count > 0)
		{
			do
			{
				_pagesSplit[0].Dispose();
				_pagesSplit.RemoveAt(0);
			}
			while (_pagesSplit.Count > 0);
		}
		bitmap.Dispose();
		tableLayoutPanel1.AutoSize = false;
		tableLayoutPanel1.AutoScroll = true;
		tableLayoutPanel1.Width = num;
		tableLayoutPanel1.Height = num2;
		foreach (Control control4 in tableLayoutPanel1.Controls)
		{
			if (control4 is Button)
			{
				control4.Visible = true;
			}
		}
	}

	private void dateTimePicker1_ValueChanged(object sender, EventArgs e)
	{
		if (dateTimePicker2.Value < dateTimePicker1.Value)
		{
			dateTimePicker2.Value = dateTimePicker1.Value;
		}
	}

	private void chkFilterActsWithVariables_CheckedChanged(object sender, EventArgs e)
	{
		getActTypes();
		Settings.Default.Capacity_Filter_Acts_With_Variables = chkFilterActsWithVariables.Checked;
		Settings.Default.Save();
	}

	private void getActTypes()
	{
		if (chkFilterActsWithVariables.Checked)
		{
			lbActivityType.DataSource = actTypes.Where((JobActivityType a) => Form1.dtCapacityVariables.Where((EvenMoreAwareDataSet.Capacity_VariableRow cv) => cv.Activity_Type_Id == a.JobActivityTypeId).FirstOrDefault() != null).ToList();
		}
		else
		{
			lbActivityType.DataSource = actTypes;
		}
		lbActivityType.ClearSelected();
	}

	private void timer1_Tick(object sender, EventArgs e)
	{
		try
		{
			List<JTProcess> processes = MWConnect.GetProcesses();
			client.DownloadString(compLocRow.Company_Location_Moraware_Url.TrimEnd('/') + "/d.aspx");
		}
		catch
		{
		}
	}

	private void pbHelp_Click(object sender, EventArgs e)
	{
		EvenMoreAwareDashboard.Help.openHelp(2, Form1);
	}

	private void lbAssignee_Validated(object sender, EventArgs e)
	{
	}

	private void btnCapacityLocks_Click(object sender, EventArgs e)
	{
		dtCapacityLocks = Form1.serviceClient.GetCapacity_Locks(compLocRow.Company_Location_Id, Settings.Default.EvenMoreAwarePassword, DateTime.Now.AddDays(-30.0));
		frmCapacityLocks frmCapacityLocks2 = new frmCapacityLocks();
		frmCapacityLocks2.Owner = this;
		frmCapacityLocks2.ShowDialog();
		dtCapacityLocks = Form1.serviceClient.GetCapacity_Locks(compLocRow.Company_Location_Id, Settings.Default.EvenMoreAwarePassword, DateTime.Now.AddDays(-30.0));
		updateLockBtnCount();
	}

	private void updateLockBtnCount()
	{
		if (dtCapacityLocks.Count > 0)
		{
			btnCapacityLocks.Text = "Capacity Locks: " + dtCapacityLocks.Count;
		}
	}

	protected override void Dispose(bool disposing)
	{
		if (disposing && components != null)
		{
			components.Dispose();
		}
		base.Dispose(disposing);
	}

	private void InitializeComponent()
	{
		this.components = new System.ComponentModel.Container();
		System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(EvenMoreAwareDashboard.frmCapacity));
		this.groupBox1 = new System.Windows.Forms.GroupBox();
		this.pbHelp = new System.Windows.Forms.PictureBox();
		this.chkIgnoreCancelled = new System.Windows.Forms.CheckBox();
		this.btnManageCapacityVariables = new System.Windows.Forms.Button();
		this.lblStatus = new System.Windows.Forms.Label();
		this.cbCompanyLocation = new System.Windows.Forms.ComboBox();
		this.lblCompanyLocation = new System.Windows.Forms.Label();
		this.btnPrintPreview = new System.Windows.Forms.Button();
		this.btnPrint = new System.Windows.Forms.Button();
		this.chkShowCharts = new System.Windows.Forms.CheckBox();
		this.btnRunReport = new System.Windows.Forms.Button();
		this.dateTimePicker1 = new System.Windows.Forms.DateTimePicker();
		this.label1 = new System.Windows.Forms.Label();
		this.label2 = new System.Windows.Forms.Label();
		this.dateTimePicker2 = new System.Windows.Forms.DateTimePicker();
		this.tableLayoutPanel1 = new System.Windows.Forms.TableLayoutPanel();
		this.groupBox2 = new System.Windows.Forms.GroupBox();
		this.chkFilterActsWithVariables = new System.Windows.Forms.CheckBox();
		this.btnClearAct = new System.Windows.Forms.Button();
		this.btnClear = new System.Windows.Forms.Button();
		this.label5 = new System.Windows.Forms.Label();
		this.label4 = new System.Windows.Forms.Label();
		this.lbAssignee = new System.Windows.Forms.ListBox();
		this.lbActivityType = new System.Windows.Forms.ListBox();
		this.toolTip1 = new System.Windows.Forms.ToolTip(this.components);
		this.printDialog1 = new System.Windows.Forms.PrintDialog();
		this.timer1 = new System.Windows.Forms.Timer(this.components);
		this.btnCapacityLocks = new System.Windows.Forms.Button();
		this.groupBox1.SuspendLayout();
		((System.ComponentModel.ISupportInitialize)this.pbHelp).BeginInit();
		this.groupBox2.SuspendLayout();
		base.SuspendLayout();
		this.groupBox1.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right;
		this.groupBox1.Controls.Add(this.pbHelp);
		this.groupBox1.Controls.Add(this.chkIgnoreCancelled);
		this.groupBox1.Controls.Add(this.btnManageCapacityVariables);
		this.groupBox1.Controls.Add(this.lblStatus);
		this.groupBox1.Controls.Add(this.cbCompanyLocation);
		this.groupBox1.Controls.Add(this.lblCompanyLocation);
		this.groupBox1.Controls.Add(this.btnPrintPreview);
		this.groupBox1.Controls.Add(this.btnPrint);
		this.groupBox1.Controls.Add(this.chkShowCharts);
		this.groupBox1.Controls.Add(this.btnRunReport);
		this.groupBox1.Controls.Add(this.dateTimePicker1);
		this.groupBox1.Controls.Add(this.label1);
		this.groupBox1.Controls.Add(this.label2);
		this.groupBox1.Controls.Add(this.dateTimePicker2);
		this.groupBox1.Location = new System.Drawing.Point(12, 12);
		this.groupBox1.Name = "groupBox1";
		this.groupBox1.Size = new System.Drawing.Size(980, 77);
		this.groupBox1.TabIndex = 7;
		this.groupBox1.TabStop = false;
		this.groupBox1.Text = "Report Settings";
		this.pbHelp.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
		this.pbHelp.Cursor = System.Windows.Forms.Cursors.Hand;
		this.pbHelp.Image = (System.Drawing.Image)resources.GetObject("pbHelp.Image");
		this.pbHelp.Location = new System.Drawing.Point(839, 46);
		this.pbHelp.Name = "pbHelp";
		this.pbHelp.Size = new System.Drawing.Size(20, 20);
		this.pbHelp.SizeMode = System.Windows.Forms.PictureBoxSizeMode.AutoSize;
		this.pbHelp.TabIndex = 118;
		this.pbHelp.TabStop = false;
		this.toolTip1.SetToolTip(this.pbHelp, "Open help.");
		this.pbHelp.Click += new System.EventHandler(pbHelp_Click);
		this.chkIgnoreCancelled.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
		this.chkIgnoreCancelled.AutoSize = true;
		this.chkIgnoreCancelled.Checked = true;
		this.chkIgnoreCancelled.CheckState = System.Windows.Forms.CheckState.Checked;
		this.chkIgnoreCancelled.Location = new System.Drawing.Point(664, 48);
		this.chkIgnoreCancelled.Name = "chkIgnoreCancelled";
		this.chkIgnoreCancelled.Size = new System.Drawing.Size(169, 17);
		this.chkIgnoreCancelled.TabIndex = 38;
		this.chkIgnoreCancelled.Text = "Ignore Status Type: Cancelled";
		this.chkIgnoreCancelled.UseVisualStyleBackColor = true;
		this.btnManageCapacityVariables.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
		this.btnManageCapacityVariables.Image = EvenMoreAwareDashboard.Properties.Resources.config_16x16;
		this.btnManageCapacityVariables.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
		this.btnManageCapacityVariables.Location = new System.Drawing.Point(865, 44);
		this.btnManageCapacityVariables.Name = "btnManageCapacityVariables";
		this.btnManageCapacityVariables.Size = new System.Drawing.Size(109, 24);
		this.btnManageCapacityVariables.TabIndex = 37;
		this.btnManageCapacityVariables.Text = "Variables";
		this.btnManageCapacityVariables.UseVisualStyleBackColor = true;
		this.btnManageCapacityVariables.Click += new System.EventHandler(btnManageCapacityVariables_Click);
		this.lblStatus.AutoSize = true;
		this.lblStatus.Location = new System.Drawing.Point(291, 49);
		this.lblStatus.Name = "lblStatus";
		this.lblStatus.Size = new System.Drawing.Size(69, 13);
		this.lblStatus.TabIndex = 36;
		this.lblStatus.Text = "Status: Idle...";
		this.cbCompanyLocation.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
		this.cbCompanyLocation.FormattingEnabled = true;
		this.cbCompanyLocation.Location = new System.Drawing.Point(112, 46);
		this.cbCompanyLocation.Name = "cbCompanyLocation";
		this.cbCompanyLocation.Size = new System.Drawing.Size(173, 21);
		this.cbCompanyLocation.TabIndex = 33;
		this.cbCompanyLocation.SelectedIndexChanged += new System.EventHandler(cbCompanyLocation_SelectedIndexChanged);
		this.lblCompanyLocation.AutoSize = true;
		this.lblCompanyLocation.Location = new System.Drawing.Point(11, 49);
		this.lblCompanyLocation.Name = "lblCompanyLocation";
		this.lblCompanyLocation.Size = new System.Drawing.Size(95, 13);
		this.lblCompanyLocation.TabIndex = 32;
		this.lblCompanyLocation.Text = "Company Location";
		this.btnPrintPreview.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
		this.btnPrintPreview.Image = EvenMoreAwareDashboard.Properties.Resources.find;
		this.btnPrintPreview.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
		this.btnPrintPreview.Location = new System.Drawing.Point(739, 14);
		this.btnPrintPreview.Name = "btnPrintPreview";
		this.btnPrintPreview.Size = new System.Drawing.Size(120, 24);
		this.btnPrintPreview.TabIndex = 31;
		this.btnPrintPreview.Text = "Print Preview";
		this.btnPrintPreview.UseVisualStyleBackColor = true;
		this.btnPrintPreview.Click += new System.EventHandler(btnPrintPreview_Click);
		this.btnPrint.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
		this.btnPrint.Image = EvenMoreAwareDashboard.Properties.Resources.printer;
		this.btnPrint.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
		this.btnPrint.Location = new System.Drawing.Point(865, 14);
		this.btnPrint.Name = "btnPrint";
		this.btnPrint.Size = new System.Drawing.Size(109, 24);
		this.btnPrint.TabIndex = 30;
		this.btnPrint.Text = "Print";
		this.btnPrint.UseVisualStyleBackColor = true;
		this.btnPrint.Click += new System.EventHandler(btnPrint_Click);
		this.chkShowCharts.AutoSize = true;
		this.chkShowCharts.Checked = true;
		this.chkShowCharts.CheckState = System.Windows.Forms.CheckState.Checked;
		this.chkShowCharts.Location = new System.Drawing.Point(523, 21);
		this.chkShowCharts.Name = "chkShowCharts";
		this.chkShowCharts.Size = new System.Drawing.Size(86, 17);
		this.chkShowCharts.TabIndex = 29;
		this.chkShowCharts.Text = "Show Charts";
		this.chkShowCharts.UseVisualStyleBackColor = true;
		this.btnRunReport.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
		this.btnRunReport.Image = EvenMoreAwareDashboard.Properties.Resources.arrow_refresh;
		this.btnRunReport.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
		this.btnRunReport.Location = new System.Drawing.Point(615, 14);
		this.btnRunReport.Name = "btnRunReport";
		this.btnRunReport.Size = new System.Drawing.Size(118, 24);
		this.btnRunReport.TabIndex = 9;
		this.btnRunReport.Text = "Run Report";
		this.btnRunReport.UseVisualStyleBackColor = true;
		this.btnRunReport.Click += new System.EventHandler(btnRunReport_Click);
		this.dateTimePicker1.Location = new System.Drawing.Point(85, 19);
		this.dateTimePicker1.Name = "dateTimePicker1";
		this.dateTimePicker1.Size = new System.Drawing.Size(200, 20);
		this.dateTimePicker1.TabIndex = 1;
		this.dateTimePicker1.ValueChanged += new System.EventHandler(dateTimePicker1_ValueChanged);
		this.label1.AutoSize = true;
		this.label1.Location = new System.Drawing.Point(11, 25);
		this.label1.Name = "label1";
		this.label1.Size = new System.Drawing.Size(68, 13);
		this.label1.TabIndex = 0;
		this.label1.Text = "Date Range:";
		this.label2.AutoSize = true;
		this.label2.Location = new System.Drawing.Point(291, 25);
		this.label2.Name = "label2";
		this.label2.Size = new System.Drawing.Size(20, 13);
		this.label2.TabIndex = 2;
		this.label2.Text = "To";
		this.dateTimePicker2.Location = new System.Drawing.Point(317, 19);
		this.dateTimePicker2.Name = "dateTimePicker2";
		this.dateTimePicker2.Size = new System.Drawing.Size(200, 20);
		this.dateTimePicker2.TabIndex = 3;
		this.tableLayoutPanel1.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom;
		this.tableLayoutPanel1.AutoScroll = true;
		this.tableLayoutPanel1.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink;
		this.tableLayoutPanel1.BackColor = System.Drawing.Color.White;
		this.tableLayoutPanel1.ColumnCount = 1;
		this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100f));
		this.tableLayoutPanel1.Location = new System.Drawing.Point(211, 95);
		this.tableLayoutPanel1.Name = "tableLayoutPanel1";
		this.tableLayoutPanel1.RowCount = 1;
		this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle());
		this.tableLayoutPanel1.Size = new System.Drawing.Size(791, 584);
		this.tableLayoutPanel1.TabIndex = 8;
		this.groupBox2.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left;
		this.groupBox2.Controls.Add(this.chkFilterActsWithVariables);
		this.groupBox2.Controls.Add(this.btnClearAct);
		this.groupBox2.Controls.Add(this.btnClear);
		this.groupBox2.Controls.Add(this.label5);
		this.groupBox2.Controls.Add(this.label4);
		this.groupBox2.Controls.Add(this.lbAssignee);
		this.groupBox2.Controls.Add(this.lbActivityType);
		this.groupBox2.Location = new System.Drawing.Point(12, 143);
		this.groupBox2.Name = "groupBox2";
		this.groupBox2.Size = new System.Drawing.Size(193, 536);
		this.groupBox2.TabIndex = 9;
		this.groupBox2.TabStop = false;
		this.groupBox2.Text = "Capacity Type(s)";
		this.chkFilterActsWithVariables.AutoSize = true;
		this.chkFilterActsWithVariables.Location = new System.Drawing.Point(6, 53);
		this.chkFilterActsWithVariables.Name = "chkFilterActsWithVariables";
		this.chkFilterActsWithVariables.Size = new System.Drawing.Size(145, 17);
		this.chkFilterActsWithVariables.TabIndex = 13;
		this.chkFilterActsWithVariables.Text = "Show only with variables.";
		this.chkFilterActsWithVariables.UseVisualStyleBackColor = true;
		this.chkFilterActsWithVariables.CheckedChanged += new System.EventHandler(chkFilterActsWithVariables_CheckedChanged);
		this.btnClearAct.Image = EvenMoreAwareDashboard.Properties.Resources.delete1;
		this.btnClearAct.Location = new System.Drawing.Point(158, 47);
		this.btnClearAct.Name = "btnClearAct";
		this.btnClearAct.Size = new System.Drawing.Size(29, 23);
		this.btnClearAct.TabIndex = 12;
		this.toolTip1.SetToolTip(this.btnClearAct, "Clear activities.");
		this.btnClearAct.UseVisualStyleBackColor = true;
		this.btnClearAct.Click += new System.EventHandler(btnClearAct_Click);
		this.btnClear.Anchor = System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left;
		this.btnClear.Image = EvenMoreAwareDashboard.Properties.Resources.delete1;
		this.btnClear.Location = new System.Drawing.Point(157, 302);
		this.btnClear.Name = "btnClear";
		this.btnClear.Size = new System.Drawing.Size(29, 23);
		this.btnClear.TabIndex = 11;
		this.toolTip1.SetToolTip(this.btnClear, "Clear assignees.");
		this.btnClear.UseVisualStyleBackColor = true;
		this.btnClear.Click += new System.EventHandler(btnClear_Click);
		this.label5.AutoSize = true;
		this.label5.Location = new System.Drawing.Point(6, 21);
		this.label5.Name = "label5";
		this.label5.Size = new System.Drawing.Size(114, 26);
		this.label5.TabIndex = 4;
		this.label5.Text = "(Required) - By Activity\r\nCtrl-Click for multiple";
		this.label4.Anchor = System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left;
		this.label4.AutoSize = true;
		this.label4.Location = new System.Drawing.Point(6, 312);
		this.label4.Name = "label4";
		this.label4.Size = new System.Drawing.Size(130, 13);
		this.label4.TabIndex = 3;
		this.label4.Text = "(Optional) - By Assignee(s)";
		this.lbAssignee.Anchor = System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left;
		this.lbAssignee.FormattingEnabled = true;
		this.lbAssignee.HorizontalScrollbar = true;
		this.lbAssignee.Location = new System.Drawing.Point(6, 331);
		this.lbAssignee.Name = "lbAssignee";
		this.lbAssignee.SelectionMode = System.Windows.Forms.SelectionMode.MultiExtended;
		this.lbAssignee.Size = new System.Drawing.Size(180, 199);
		this.lbAssignee.TabIndex = 2;
		this.lbAssignee.Validated += new System.EventHandler(lbAssignee_Validated);
		this.lbActivityType.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left;
		this.lbActivityType.FormattingEnabled = true;
		this.lbActivityType.HorizontalScrollbar = true;
		this.lbActivityType.Location = new System.Drawing.Point(6, 76);
		this.lbActivityType.Name = "lbActivityType";
		this.lbActivityType.SelectionMode = System.Windows.Forms.SelectionMode.MultiExtended;
		this.lbActivityType.Size = new System.Drawing.Size(180, 212);
		this.lbActivityType.TabIndex = 1;
		this.printDialog1.UseEXDialog = true;
		this.timer1.Interval = 300000;
		this.timer1.Tick += new System.EventHandler(timer1_Tick);
		this.btnCapacityLocks.Image = EvenMoreAwareDashboard.Properties.Resources.padlock;
		this.btnCapacityLocks.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
		this.btnCapacityLocks.Location = new System.Drawing.Point(12, 95);
		this.btnCapacityLocks.Name = "btnCapacityLocks";
		this.btnCapacityLocks.Size = new System.Drawing.Size(193, 42);
		this.btnCapacityLocks.TabIndex = 10;
		this.btnCapacityLocks.Text = "Capacity Locks";
		this.btnCapacityLocks.UseVisualStyleBackColor = true;
		this.btnCapacityLocks.Click += new System.EventHandler(btnCapacityLocks_Click);
		base.AutoScaleDimensions = new System.Drawing.SizeF(6f, 13f);
		base.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
		base.ClientSize = new System.Drawing.Size(1004, 691);
		base.Controls.Add(this.btnCapacityLocks);
		base.Controls.Add(this.groupBox2);
		base.Controls.Add(this.tableLayoutPanel1);
		base.Controls.Add(this.groupBox1);
		base.Icon = (System.Drawing.Icon)resources.GetObject("$this.Icon");
		this.MinimumSize = new System.Drawing.Size(1020, 730);
		base.Name = "frmCapacity";
		base.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
		this.Text = "EvenMoreAware - Capacity Report";
		base.FormClosing += new System.Windows.Forms.FormClosingEventHandler(frmCapacity_FormClosing);
		base.Load += new System.EventHandler(frmCapacity_Load);
		this.groupBox1.ResumeLayout(false);
		this.groupBox1.PerformLayout();
		((System.ComponentModel.ISupportInitialize)this.pbHelp).EndInit();
		this.groupBox2.ResumeLayout(false);
		this.groupBox2.PerformLayout();
		base.ResumeLayout(false);
	}
}
