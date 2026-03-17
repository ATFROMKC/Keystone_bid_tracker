// EvenMoreAwareDashboard, Version=1.1.0.0, Culture=neutral, PublicKeyToken=null
// EvenMoreAwareDashboard.frmJobSearch
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;
using EvenMoreAwareDashboard;
using EvenMoreAwareDashboard.Properties;
using Moraware.JobTrackerAPI5;

public class frmJobSearch : Form
{
	private frmMap frmMap = null;

	public bool selected = false;

	private IContainer components = null;

	private GroupBox groupBox1;

	private Button btnCancel;

	private Button button1;

	private TextBox txtSearch;

	private Label label2;

	private Button btnSearch;

	public DataGridView dataGridView1;

	private Label label1;

	private ListBox lbFields;

	private Button btnClear;

	private ToolTip toolTip1;

	public frmJobSearch()
	{
		InitializeComponent();
	}

	private void frmJobSearch_Load(object sender, EventArgs e)
	{
		if (base.Owner is frmMap)
		{
			frmMap = (frmMap)base.Owner;
			loadJobFields(frmMap);
		}
		base.ActiveControl = txtSearch;
	}

	private void loadJobFields(Form frm)
	{
		if (frm is frmMap)
		{
			lbFields.DataSource = (from cf in frmMap.MWConnect.GetCustomJobFieldTypes(includeInactive_: false)
				orderby cf.CustomFieldTypeName
				where cf.CustomFieldDataType != CustomFieldType.CustomFieldDataType_Enum.ListOfValues
				select cf).ToList();
		}
		lbFields.DisplayMember = "CustomFieldTypeName";
		lbFields.ValueMember = "CustomFieldTypeId";
		lbFields.ClearSelected();
	}

	private void btnCancel_Click(object sender, EventArgs e)
	{
		selected = false;
		Close();
	}

	private void button1_Click(object sender, EventArgs e)
	{
		if (dataGridView1.CurrentRow != null && MessageBox.Show("Are you sure?", "EvenMoreAware", MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question) == DialogResult.Yes)
		{
			selected = true;
			Close();
		}
	}

	private void txtSearch_TextChanged(object sender, EventArgs e)
	{
		base.AcceptButton = btnSearch;
	}

	private void btnSearch_Click(object sender, EventArgs e)
	{
		Cursor current = Cursor.Current;
		Cursor.Current = Cursors.WaitCursor;
		List<Job> dataSource = new List<Job>();
		PagingOptions pagingOptions_ = new PagingOptions(0, int.MaxValue);
		JobFilter jobFilter = new JobFilter();
		if (lbFields.SelectedItems.Count == 0)
		{
			jobFilter.AddTextFilter(JobFilter.JobTextFilterFields_Enum.Name, new TextFilter(txtSearch.Text.Trim(), exactMatch_: false));
		}
		else
		{
			jobFilter.AddJobCustomFieldFilter((int)lbFields.SelectedValue, new TextFilter(txtSearch.Text.Trim(), exactMatch_: false));
		}
		if (frmMap != null)
		{
			dataSource = frmMap.MWConnect.GetJobs(jobFilter, pagingOptions_);
		}
		dataGridView1.DataSource = dataSource;
		foreach (DataGridViewColumn column in dataGridView1.Columns)
		{
			if (column.HeaderText != "JobName")
			{
				column.Visible = false;
			}
		}
		dataGridView1.AutoResizeColumns();
		Cursor.Current = current;
	}

	private void btnClear_Click(object sender, EventArgs e)
	{
		lbFields.ClearSelected();
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
		System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(EvenMoreAwareDashboard.frmJobSearch));
		this.groupBox1 = new System.Windows.Forms.GroupBox();
		this.btnClear = new System.Windows.Forms.Button();
		this.label1 = new System.Windows.Forms.Label();
		this.lbFields = new System.Windows.Forms.ListBox();
		this.btnSearch = new System.Windows.Forms.Button();
		this.btnCancel = new System.Windows.Forms.Button();
		this.button1 = new System.Windows.Forms.Button();
		this.dataGridView1 = new System.Windows.Forms.DataGridView();
		this.txtSearch = new System.Windows.Forms.TextBox();
		this.label2 = new System.Windows.Forms.Label();
		this.toolTip1 = new System.Windows.Forms.ToolTip(this.components);
		this.groupBox1.SuspendLayout();
		((System.ComponentModel.ISupportInitialize)this.dataGridView1).BeginInit();
		base.SuspendLayout();
		this.groupBox1.Controls.Add(this.btnClear);
		this.groupBox1.Controls.Add(this.label1);
		this.groupBox1.Controls.Add(this.lbFields);
		this.groupBox1.Controls.Add(this.btnSearch);
		this.groupBox1.Controls.Add(this.btnCancel);
		this.groupBox1.Controls.Add(this.button1);
		this.groupBox1.Controls.Add(this.dataGridView1);
		this.groupBox1.Controls.Add(this.txtSearch);
		this.groupBox1.Controls.Add(this.label2);
		this.groupBox1.Location = new System.Drawing.Point(12, 12);
		this.groupBox1.Name = "groupBox1";
		this.groupBox1.Size = new System.Drawing.Size(446, 204);
		this.groupBox1.TabIndex = 0;
		this.groupBox1.TabStop = false;
		this.groupBox1.Text = "Search By Job Name OR Custom Field";
		this.btnClear.Image = EvenMoreAwareDashboard.Properties.Resources.delete1;
		this.btnClear.Location = new System.Drawing.Point(145, 24);
		this.btnClear.Name = "btnClear";
		this.btnClear.Size = new System.Drawing.Size(29, 23);
		this.btnClear.TabIndex = 10;
		this.toolTip1.SetToolTip(this.btnClear, "Clear custom field selection.");
		this.btnClear.UseVisualStyleBackColor = true;
		this.btnClear.Click += new System.EventHandler(btnClear_Click);
		this.label1.AutoSize = true;
		this.label1.Location = new System.Drawing.Point(6, 22);
		this.label1.Name = "label1";
		this.label1.Size = new System.Drawing.Size(111, 26);
		this.label1.TabIndex = 9;
		this.label1.Text = "Select custom field to \r\nsearch alternatively.";
		this.lbFields.FormattingEnabled = true;
		this.lbFields.HorizontalScrollbar = true;
		this.lbFields.Location = new System.Drawing.Point(6, 51);
		this.lbFields.Name = "lbFields";
		this.lbFields.Size = new System.Drawing.Size(169, 147);
		this.lbFields.TabIndex = 8;
		this.btnSearch.Image = EvenMoreAwareDashboard.Properties.Resources.arrow_refresh;
		this.btnSearch.Location = new System.Drawing.Point(408, 17);
		this.btnSearch.Name = "btnSearch";
		this.btnSearch.Size = new System.Drawing.Size(32, 23);
		this.btnSearch.TabIndex = 7;
		this.toolTip1.SetToolTip(this.btnSearch, "Search");
		this.btnSearch.UseVisualStyleBackColor = true;
		this.btnSearch.Click += new System.EventHandler(btnSearch_Click);
		this.btnCancel.Image = EvenMoreAwareDashboard.Properties.Resources.cancel;
		this.btnCancel.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
		this.btnCancel.Location = new System.Drawing.Point(266, 175);
		this.btnCancel.Name = "btnCancel";
		this.btnCancel.Size = new System.Drawing.Size(84, 23);
		this.btnCancel.TabIndex = 6;
		this.btnCancel.Text = "Cancel";
		this.btnCancel.UseVisualStyleBackColor = true;
		this.btnCancel.Click += new System.EventHandler(btnCancel_Click);
		this.button1.Image = EvenMoreAwareDashboard.Properties.Resources.accept;
		this.button1.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft;
		this.button1.Location = new System.Drawing.Point(356, 175);
		this.button1.Name = "button1";
		this.button1.Size = new System.Drawing.Size(84, 23);
		this.button1.TabIndex = 5;
		this.button1.Text = "Select";
		this.button1.UseVisualStyleBackColor = true;
		this.button1.Click += new System.EventHandler(button1_Click);
		this.dataGridView1.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
		this.dataGridView1.Location = new System.Drawing.Point(200, 45);
		this.dataGridView1.MultiSelect = false;
		this.dataGridView1.Name = "dataGridView1";
		this.dataGridView1.Size = new System.Drawing.Size(240, 124);
		this.dataGridView1.TabIndex = 4;
		this.txtSearch.Location = new System.Drawing.Point(259, 19);
		this.txtSearch.Name = "txtSearch";
		this.txtSearch.Size = new System.Drawing.Size(143, 20);
		this.txtSearch.TabIndex = 3;
		this.txtSearch.TextChanged += new System.EventHandler(txtSearch_TextChanged);
		this.label2.AutoSize = true;
		this.label2.Location = new System.Drawing.Point(197, 22);
		this.label2.Name = "label2";
		this.label2.Size = new System.Drawing.Size(56, 13);
		this.label2.TabIndex = 2;
		this.label2.Text = "Search for";
		base.AutoScaleDimensions = new System.Drawing.SizeF(6f, 13f);
		base.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
		base.ClientSize = new System.Drawing.Size(470, 222);
		base.Controls.Add(this.groupBox1);
		base.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow;
		base.Icon = (System.Drawing.Icon)resources.GetObject("$this.Icon");
		base.Name = "frmJobSearch";
		base.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent;
		this.Text = "EvenMoreAware - Job Search";
		base.Load += new System.EventHandler(frmJobSearch_Load);
		this.groupBox1.ResumeLayout(false);
		this.groupBox1.PerformLayout();
		((System.ComponentModel.ISupportInitialize)this.dataGridView1).EndInit();
		base.ResumeLayout(false);
	}
}
