// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Account
using System;
using Moraware.JobTrackerAPI5;

public class Account : HasCustomFieldValues
{
	internal enum AccountConditionalFieldUpdateFlags_Enum
	{
		cfufAccountName = 1,
		cfufAddress = 2,
		cfufSalesperson = 4,
		cfufAccountingId = 8,
		cfufIsInactive = 0x10,
		cfufNotes = 0x20,
		cfufCreateSeparateAddressForJob = 0x40,
		cfufPostUltimate_Account = 0x80
	}

	public enum AccountStatusType_Enum
	{
		Active = 1,
		Inactive
	}

	private Address _address;

	private string _salespersonName;

	private int? _salespersonId;

	private string _accountName;

	private string _notes;

	private string _accountingId;

	private bool _isInactive;

	private bool _createSeparateAddressForJob;

	internal bool ModifiedAccountingId => base.UpdateFlags.AreFlagsSet(8);

	internal bool ModifiedAddress
	{
		get
		{
			if (base.UpdateFlags.AreFlagsSet(2))
			{
				return true;
			}
			if (Address == null)
			{
				return false;
			}
			return Address.Modified;
		}
	}

	internal bool ModifiedIsInactive => base.UpdateFlags.AreFlagsSet(16);

	internal bool ModifiedCreateSeparateAddressForJob => base.UpdateFlags.AreFlagsSet(64);

	internal bool ModifiedNotes => base.UpdateFlags.AreFlagsSet(32);

	internal bool ModifiedSalesperson => base.UpdateFlags.AreFlagsSet(4);

	public Address Address
	{
		get
		{
			return _address;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_address = value;
		}
	}

	public string SalespersonName
	{
		get
		{
			return _salespersonName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_salespersonName = value;
			_salespersonId = null;
		}
	}

	public int? SalespersonId
	{
		get
		{
			return _salespersonId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_salespersonId = value;
			_salespersonName = null;
		}
	}

	public string Notes
	{
		get
		{
			return _notes;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(32);
			_notes = value;
		}
	}

	public string AccountingId
	{
		get
		{
			return _accountingId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			_accountingId = value;
		}
	}

	public bool IsInactive
	{
		get
		{
			return _isInactive;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(16);
			_isInactive = value;
		}
	}

	public bool CreateSeparateAddressForJob
	{
		get
		{
			return _createSeparateAddressForJob;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(64);
			_createSeparateAddressForJob = value;
		}
	}

	public AccountStatusType_Enum AccountStatus
	{
		get
		{
			if (!_isInactive)
			{
				return AccountStatusType_Enum.Active;
			}
			return AccountStatusType_Enum.Inactive;
		}
		set
		{
			if ((uint)(value - 1) <= 1u)
			{
				IsInactive = value == AccountStatusType_Enum.Inactive;
				return;
			}
			throw new Exception($"Invalid Account Status:  {value} (Id={(int)value})");
		}
	}

	internal DefaultJobTemplateContainer DefaultJobTemplates { get; } = new DefaultJobTemplateContainer();

	public JobTemplate DefaultJobTemplate
	{
		get
		{
			return GetDefaultJobTemplate();
		}
		set
		{
			SetDefaultJobTemplate(1, value);
		}
	}

	public int AccountId { get; internal set; }

	public string AccountName
	{
		get
		{
			return _accountName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_accountName = value;
		}
	}

	internal bool ModifiedAccountName => base.UpdateFlags.AreFlagsSet(1);

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (Address != null)
		{
			Address.ClearUpdateFlags();
		}
		DefaultJobTemplates.ClearUpdateFlags();
	}

	internal static string AccountStatusStringFromId(AccountStatusType_Enum accountStatus_)
	{
		return accountStatus_ switch
		{
			AccountStatusType_Enum.Active => "active", 
			AccountStatusType_Enum.Inactive => "inactive", 
			_ => throw new Exception("Unknown Account Status, " + (int)accountStatus_ + "!!!"), 
		};
	}

	public Account(string accountName_)
	{
		AccountName = accountName_;
	}

	public Account(int accountId_)
	{
		AccountId = accountId_;
	}

	internal void SetSalesperson(int? salespersonId_, string salespersonName_)
	{
		base.UpdateFlags.AddUpdateFlag(4);
		_salespersonId = salespersonId_;
		_salespersonName = salespersonName_;
	}

	public JobTemplate GetDefaultJobTemplate(int processId_ = 1)
	{
		return DefaultJobTemplates.GetJobTemplate(processId_);
	}

	public void SetDefaultJobTemplate(int processId_, JobTemplate value)
	{
		DefaultJobTemplates.SetJobTemplate(processId_, value);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AccountContact
using Moraware.JobTrackerAPI5;

public class AccountContact : JTObject
{
	internal enum AccountContactConditionalFieldUpdateFlags_Enum
	{
		cfufAddress = 1
	}

	internal bool Modified
	{
		get
		{
			bool flag = false;
			if (base.UpdateFlags.AreAnyFlagsSet(1))
			{
				return true;
			}
			if (Address == null)
			{
				return false;
			}
			return Address.Modified;
		}
	}

	public int ContactId { get; internal set; }

	public Address Address { get; }

	public int AccountId { get; internal set; }

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (Address != null)
		{
			Address.ClearUpdateFlags();
		}
	}

	internal AccountContact(int accountId_, int contactId_, Address address_)
	{
		AccountId = accountId_;
		ContactId = contactId_;
		Address = address_;
	}

	public AccountContact(int accountId_)
	{
		AccountId = accountId_;
		Address = new Address();
	}

	public AccountContact(int contactId_, int accountId_)
	{
		ContactId = contactId_;
		AccountId = accountId_;
		Address = new Address();
	}

	public AccountContact()
	{
		Address = new Address();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AccountCustomFieldType
using Moraware.JobTrackerAPI5;

public class AccountCustomFieldType : CustomFieldType
{
	internal AccountCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AccountFile
using Moraware.JobTrackerAPI5;

public class AccountFile : AttachedFile
{
	public int AccountId => base.ParentObjectId;

	public AccountFile(int id_)
		: base(id_)
	{
	}

	public AccountFile(int accountId_, string name_)
		: base(accountId_, name_)
	{
	}

	internal AccountFile(int id_, int accountId_, string name_, string description_, int? size_)
		: base(id_, accountId_, name_, description_, size_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AccountFilter
using System;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class AccountFilter
{
	public enum AccountListOfValuesFilterFields_Enum
	{
		Salesperson = 1
	}

	public enum AccountTextFilterFields_Enum
	{
		Name = 1,
		Notes
	}

	internal CustomFieldFilters ObjCustomFieldFilters { get; }

	internal List<AccountStatusFilter> AccountStatusFilters { get; }

	internal List<BuiltInListOfValuesFilter<AccountListOfValuesFilterFields_Enum>> ListOfValuesFilters { get; }

	internal List<BuiltInTextFilter<AccountTextFilterFields_Enum>> TextFilters { get; }

	public int? ViewId { get; set; }

	internal List<CustomFieldFilter> CustomFieldFilters => ObjCustomFieldFilters.CustomFieldFiltersList;

	public void AddTextFilter(AccountTextFilterFields_Enum field_, TextFilter textFilter_)
	{
		if (textFilter_ != null)
		{
			TextFilters.Add(new BuiltInTextFilter<AccountTextFilterFields_Enum>(field_, textFilter_));
		}
	}

	public void AddListOfValuesFilter(AccountListOfValuesFilterFields_Enum field_, ListOfValuesFilter listOfValuesFilter_)
	{
		if (listOfValuesFilter_ != null)
		{
			ListOfValuesFilters.Add(new BuiltInListOfValuesFilter<AccountListOfValuesFilterFields_Enum>(field_, listOfValuesFilter_));
		}
	}

	public AccountFilter()
	{
		ObjCustomFieldFilters = new CustomFieldFilters();
		AccountStatusFilters = new List<AccountStatusFilter>();
		TextFilters = new List<BuiltInTextFilter<AccountTextFilterFields_Enum>>();
		ListOfValuesFilters = new List<BuiltInListOfValuesFilter<AccountListOfValuesFilterFields_Enum>>();
	}

	public AccountFilter(Account.AccountStatusType_Enum accountStatusType_)
		: this()
	{
		switch (accountStatusType_)
		{
		case Account.AccountStatusType_Enum.Active:
			AddAccountStatusFilter(new AccountStatusFilter(invert_: false, Account.AccountStatusType_Enum.Active));
			break;
		case Account.AccountStatusType_Enum.Inactive:
			AddAccountStatusFilter(new AccountStatusFilter(invert_: false, Account.AccountStatusType_Enum.Inactive));
			break;
		default:
			throw new Exception($"Unsupported AccountStatusType:  {accountStatusType_}");
		}
	}

	public void AddAccountStatusFilter(AccountStatusFilter accountStatusFilter_)
	{
		AccountStatusFilters.Add(accountStatusFilter_);
	}

	public void AddAccountStatusFilter(Account.AccountStatusType_Enum accountStatusType_)
	{
		AccountStatusFilters.Add(new AccountStatusFilter(invert_: false, accountStatusType_));
	}

	public void AddAccountCustomFieldFilter(int customFieldId_, ICustomFieldFilter filter_)
	{
		ObjCustomFieldFilters.AddCustomFieldFilter(customFieldId_, filter_, CustomFieldType.CustomFieldType_Enum.Account);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AccountPriceList
using Moraware.JobTrackerAPI5;

public class AccountPriceList
{
	internal enum AccountPriceListConditionalFieldUpdateFlags_Enum
	{
		cfufTaxPercent = 1,
		cfufDiscountPercent = 2,
		cfufIsInactive = 4,
		cfufPostUltimate_AccountPriceList = 8
	}

	private PriceList m_priceList;

	private int m_accountId;

	private string m_accountName;

	private decimal? m_taxPercent;

	private decimal? m_discountPercent;

	private bool m_isInactive;

	private UpdateFlags m_updateFlags = new UpdateFlags();

	internal UpdateFlags UpdateFlags => m_updateFlags;

	internal bool ModifiedTaxPercent => UpdateFlags.AreFlagsSet(1);

	internal bool ModifiedIsInactive => UpdateFlags.AreFlagsSet(4);

	internal bool ModifiedDiscountPercent => UpdateFlags.AreFlagsSet(2);

	public PriceList PriceList => m_priceList;

	public int AccountId => m_accountId;

	public string AccountName => m_accountName;

	public decimal? TaxPercent
	{
		get
		{
			return m_taxPercent;
		}
		set
		{
			UpdateFlags.AddUpdateFlag(1);
			m_taxPercent = value;
		}
	}

	public decimal? DiscountPercent
	{
		get
		{
			return m_discountPercent;
		}
		set
		{
			UpdateFlags.AddUpdateFlag(2);
			m_discountPercent = value;
		}
	}

	public bool IsInactive
	{
		get
		{
			return m_isInactive;
		}
		set
		{
			UpdateFlags.AddUpdateFlag(4);
			m_isInactive = value;
		}
	}

	internal void ClearUpdateFlags()
	{
		UpdateFlags.ClearUpdateFlags();
	}

	internal AccountPriceList(int accountId_, string accountName_, PriceList priceList_)
	{
		m_accountId = accountId_;
		m_priceList = priceList_;
		m_accountName = accountName_;
	}

	public AccountPriceList(int accountId_, int priceListId_)
	{
		m_accountId = accountId_;
		m_priceList = new PriceList(priceListId_, "", null, isInactive_: false);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AccountStatusFilter
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class AccountStatusFilter : Filter
{
	private GenericListOfValuesFilter<Account.AccountStatusType_Enum, AccountStatusFilterValues> _genericLOVFilter;

	public bool Invert
	{
		get
		{
			return _genericLOVFilter.Invert;
		}
		set
		{
			_genericLOVFilter.Invert = value;
		}
	}

	public AccountStatusFilterValues Values => _genericLOVFilter.Values;

	public AccountStatusFilter()
		: this(invert_: false, null)
	{
	}

	public AccountStatusFilter(bool invert_, AccountStatusFilterValues values_)
	{
		_genericLOVFilter = new GenericListOfValuesFilter<Account.AccountStatusType_Enum, AccountStatusFilterValues>(invert_, values_);
	}

	public AccountStatusFilter(bool invert_, IEnumerable<Account.AccountStatusType_Enum> values_)
		: this(invert_, new AccountStatusFilterValues(values_))
	{
	}

	public AccountStatusFilter(bool invert_, Account.AccountStatusType_Enum value_)
		: this(invert_, new Account.AccountStatusType_Enum[1] { value_ })
	{
	}

	public AccountStatusFilter(Account.AccountStatusType_Enum value_)
		: this(invert_: false, new Account.AccountStatusType_Enum[1] { value_ })
	{
	}

	public override object Clone()
	{
		return new AccountStatusFilter(Invert, Values);
	}

	public string BuildDescription(string fieldName_)
	{
		return _genericLOVFilter.BuildDescription(fieldName_, modGlobals.BuildDictionaryFromEnumeration(new Account.AccountStatusType_Enum[2]
		{
			Account.AccountStatusType_Enum.Active,
			Account.AccountStatusType_Enum.Inactive
		}));
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AccountStatusFilterValues
using System;
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class AccountStatusFilterValues : IGenericListOfValuesFilterValues<Account.AccountStatusType_Enum>, IEnumerable<Account.AccountStatusType_Enum>, IEnumerable, ICloneable
{
	private GenericListOfValuesFilterValues<Account.AccountStatusType_Enum> _genericLOVFilterValues;

	public List<Account.AccountStatusType_Enum> Values => _genericLOVFilterValues.Values;

	public IEnumerator<Account.AccountStatusType_Enum> GetEnumerator()
	{
		return _genericLOVFilterValues.GetEnumerator();
	}

	IEnumerator<Account.AccountStatusType_Enum> IEnumerable<Account.AccountStatusType_Enum>.GetEnumerator()
	{
		return GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}

	public AccountStatusFilterValues()
	{
	}

	public AccountStatusFilterValues(IEnumerable<Account.AccountStatusType_Enum> values_)
	{
		_genericLOVFilterValues = new GenericListOfValuesFilterValues<Account.AccountStatusType_Enum>(values_);
	}

	bool IGenericListOfValuesFilterValues<Account.AccountStatusType_Enum>.DoIncludeNone()
	{
		return DoIncludeNone();
	}

	internal bool DoIncludeNone()
	{
		return _genericLOVFilterValues.DoIncludeNone();
	}

	object ICloneable.Clone()
	{
		return Clone();
	}

	internal object Clone()
	{
		return new AccountStatusFilterValues(Values);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Address
using Moraware.JobTrackerAPI5;

public class Address : JTObject
{
	internal enum AddressConditionalFieldUpdateFlags_Enum
	{
		cfufContactName = 1,
		cfufAddressLine1 = 2,
		cfufAddressLine2 = 4,
		cfufCity = 8,
		cfufState = 16,
		cfufZip = 32,
		cfufCountry = 64,
		cfufPhone = 128,
		cfufPhone2 = 256,
		cfufCell = 512,
		cfufFax = 1024,
		cfufEmail = 2048,
		cfufNotes = 4096,
		cfufAll = 8191,
		cfufPostUltimate_Address = 8192
	}

	private string m_contactName;

	private string m_addressLine1;

	private string m_addressLine2;

	private string m_city;

	private string m_state;

	private string m_zip;

	private string m_country;

	private string m_phone;

	private string m_phone2;

	private string m_cell;

	private string m_fax;

	private string m_email;

	private string m_notes;

	internal bool Modified => base.UpdateFlags.AreAnyFlagsSet(8191);

	internal bool ModifiedContactName => base.UpdateFlags.AreFlagsSet(1);

	internal bool ModifiedAddressLine1 => base.UpdateFlags.AreFlagsSet(2);

	internal bool ModifiedAddressLine2 => base.UpdateFlags.AreFlagsSet(4);

	internal bool ModifiedCity => base.UpdateFlags.AreFlagsSet(8);

	internal bool ModifiedState => base.UpdateFlags.AreFlagsSet(16);

	internal bool ModifiedZip => base.UpdateFlags.AreFlagsSet(32);

	internal bool ModifiedCountry => base.UpdateFlags.AreFlagsSet(64);

	internal bool ModifiedPhone => base.UpdateFlags.AreFlagsSet(128);

	internal bool ModifiedPhone2 => base.UpdateFlags.AreFlagsSet(256);

	internal bool ModifiedCell => base.UpdateFlags.AreFlagsSet(512);

	internal bool ModifiedFax => base.UpdateFlags.AreFlagsSet(1024);

	internal bool ModifiedEmail => base.UpdateFlags.AreFlagsSet(2048);

	internal bool ModifiedNotes => base.UpdateFlags.AreFlagsSet(4096);

	public string ContactName
	{
		get
		{
			return m_contactName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			m_contactName = value;
		}
	}

	public string AddressLine1
	{
		get
		{
			return m_addressLine1;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			m_addressLine1 = value;
		}
	}

	public string AddressLine2
	{
		get
		{
			return m_addressLine2;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			m_addressLine2 = value;
		}
	}

	public string City
	{
		get
		{
			return m_city;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			m_city = value;
		}
	}

	public string State
	{
		get
		{
			return m_state;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(16);
			m_state = value;
		}
	}

	public string Zip
	{
		get
		{
			return m_zip;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(32);
			m_zip = value;
		}
	}

	public string Country
	{
		get
		{
			return m_country;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(64);
			m_country = value;
		}
	}

	public string Phone
	{
		get
		{
			return m_phone;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(128);
			m_phone = value;
		}
	}

	public string Phone2
	{
		get
		{
			return m_phone2;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(256);
			m_phone2 = value;
		}
	}

	public string Cell
	{
		get
		{
			return m_cell;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(512);
			m_cell = value;
		}
	}

	public string Fax
	{
		get
		{
			return m_fax;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1024);
			m_fax = value;
		}
	}

	public string Email
	{
		get
		{
			return m_email;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2048);
			m_email = value;
		}
	}

	public string Notes
	{
		get
		{
			return m_notes;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4096);
			m_notes = value;
		}
	}

	internal Address(string contactName_, string addressLine1_, string addressLine2_, string city_, string state_, string zip_, string country_, string phone_, string phone2_, string cell_, string fax_, string email_, string notes_)
	{
		ContactName = contactName_;
		AddressLine1 = addressLine1_;
		AddressLine2 = addressLine2_;
		City = city_;
		State = state_;
		Zip = zip_;
		Country = country_;
		Phone = phone_;
		Phone2 = phone2_;
		Cell = cell_;
		Fax = fax_;
		Email = email_;
		Notes = notes_;
	}

	public Address()
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Allocation
using Moraware.JobTrackerAPI5;

public class Allocation : JTObject
{
	internal enum PurchaseProductVariantAllocationConditionalFieldUpdateFlags_Enum
	{
		cfufQuantity = 1,
		cfufPostUltimate_PurchaseProductVariantAllocation
	}

	private int m_jobId;

	private string m_jobName;

	private int m_jobActivityId;

	private int m_jobActivityTypeId;

	private string m_jobActivityTypeName;

	private int m_purchaseProductVariantId;

	private string m_purchaseProductVariantName;

	private PurchaseProductVariant m_ppvForCreate;

	private decimal m_quantity;

	public decimal Quantity
	{
		get
		{
			return m_quantity;
		}
		set
		{
			m_quantity = value;
			base.UpdateFlags.AddUpdateFlag(1);
		}
	}

	internal bool ModifiedQuantity => base.UpdateFlags.AreAnyFlagsSet(1);

	public int PurchaseProductVariantId => m_purchaseProductVariantId;

	public string PurchaseProductVariantName => m_purchaseProductVariantName;

	public int JobId => m_jobId;

	public string JobName => m_jobName;

	public int JobActivityId => m_jobActivityId;

	public int JobActivityTypeId => m_jobActivityTypeId;

	public string JobActivityTypeName => m_jobActivityTypeName;

	internal PurchaseProductVariant PurchaseProductVariantForCreate
	{
		get
		{
			return m_ppvForCreate;
		}
		set
		{
			m_ppvForCreate = value;
		}
	}

	internal Allocation(PurchaseProductVariant ppvForCreate_, int pvId_, string pvName_, int jobId_, string jobName_, int jaId_, int atId_, string atName_, decimal quantity_)
	{
		m_ppvForCreate = ppvForCreate_;
		m_quantity = quantity_;
		m_jobId = jobId_;
		m_jobName = jobName_;
		m_jobActivityId = jaId_;
		m_jobActivityTypeId = atId_;
		m_jobActivityTypeName = atName_;
		m_purchaseProductVariantId = pvId_;
		m_purchaseProductVariantName = pvName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.APIException
using System;
using System.Xml;
using Moraware.JobTrackerAPI5;

public class APIException : Exception
{
	public enum APIErrorCodes_Enum
	{
		SessionTimedOut = 1,
		InsufficientSecurityPrivileges = 2,
		UnsupportedVersion = 3,
		InvalidRequestDocument = 4,
		UnsupportedCommand = 5,
		LoginFailed = 6,
		NonExistentObject = 7,
		Duplicate = 8,
		CorruptFileTransfer = 9,
		FileAlreadyExists = 10,
		LicenseRestrictionExceeded = 11,
		InvalidLicense = 12,
		DependecyConflict = 13,
		SystemTemporarilyUnavailable = 14,
		GeneralException = 1000
	}

	private XmlDocument m_originalDocument;

	private APIErrorCodes_Enum m_APIErrorCode = APIErrorCodes_Enum.GeneralException;

	public APIErrorCodes_Enum APIErrorCode => m_APIErrorCode;

	public XmlDocument OriginalDocument
	{
		get
		{
			return m_originalDocument;
		}
		set
		{
			m_originalDocument = value;
		}
	}

	public static string APIErrorCodeDescription(APIErrorCodes_Enum apiErrorCode_)
	{
		return apiErrorCode_ switch
		{
			APIErrorCodes_Enum.GeneralException => "General exception", 
			APIErrorCodes_Enum.InsufficientSecurityPrivileges => "Insufficient security privileges", 
			APIErrorCodes_Enum.SessionTimedOut => "Session Timed Out", 
			APIErrorCodes_Enum.UnsupportedVersion => "Unsupported API Version", 
			APIErrorCodes_Enum.InvalidRequestDocument => "Invalid Request Document", 
			APIErrorCodes_Enum.UnsupportedCommand => "Unsupported command", 
			APIErrorCodes_Enum.LoginFailed => "Login Failed", 
			APIErrorCodes_Enum.NonExistentObject => "Object does not exist", 
			APIErrorCodes_Enum.Duplicate => "Duplicate object:  Creating/Updating would cause a conflict with an existing object", 
			APIErrorCodes_Enum.CorruptFileTransfer => "The size/checksums of the transfered file is incorrect.", 
			APIErrorCodes_Enum.FileAlreadyExists => "An attempt was made to overwrite an existing file, without explictly opting to do so.", 
			APIErrorCodes_Enum.LicenseRestrictionExceeded => "A limit placed on the license key (eg. Attached file size, Number of users, etc.) has been exceeded.", 
			APIErrorCodes_Enum.InvalidLicense => "Invalid license key.", 
			APIErrorCodes_Enum.DependecyConflict => "The action could not be performed due to one or more dependencies.", 
			APIErrorCodes_Enum.SystemTemporarilyUnavailable => "The system is temporarily unavailable\r\n(for example, as a result of a version upgrade that is in progress)", 
			_ => string.Concat("Unknown error code (", apiErrorCode_, ")"), 
		};
	}

	public static bool ConvertToAPIErrorCode(string strErrorCode_, ref APIErrorCodes_Enum apiErrorCode_)
	{
		if (string.IsNullOrEmpty(strErrorCode_))
		{
			return false;
		}
		APIErrorCodes_Enum aPIErrorCodes_Enum = (APIErrorCodes_Enum)0;
		try
		{
			aPIErrorCodes_Enum = (APIErrorCodes_Enum)Convert.ToInt32(strErrorCode_);
		}
		catch
		{
			return false;
		}
		switch (aPIErrorCodes_Enum)
		{
		case APIErrorCodes_Enum.GeneralException:
			apiErrorCode_ = APIErrorCodes_Enum.GeneralException;
			break;
		case APIErrorCodes_Enum.InsufficientSecurityPrivileges:
			apiErrorCode_ = APIErrorCodes_Enum.InsufficientSecurityPrivileges;
			break;
		case APIErrorCodes_Enum.InvalidRequestDocument:
			apiErrorCode_ = APIErrorCodes_Enum.InvalidRequestDocument;
			break;
		case APIErrorCodes_Enum.LoginFailed:
			apiErrorCode_ = APIErrorCodes_Enum.LoginFailed;
			break;
		case APIErrorCodes_Enum.NonExistentObject:
			apiErrorCode_ = APIErrorCodes_Enum.NonExistentObject;
			break;
		case APIErrorCodes_Enum.SessionTimedOut:
			apiErrorCode_ = APIErrorCodes_Enum.SessionTimedOut;
			break;
		case APIErrorCodes_Enum.UnsupportedCommand:
			apiErrorCode_ = APIErrorCodes_Enum.UnsupportedCommand;
			break;
		case APIErrorCodes_Enum.UnsupportedVersion:
			apiErrorCode_ = APIErrorCodes_Enum.UnsupportedVersion;
			break;
		case APIErrorCodes_Enum.Duplicate:
			apiErrorCode_ = APIErrorCodes_Enum.Duplicate;
			break;
		case APIErrorCodes_Enum.CorruptFileTransfer:
			apiErrorCode_ = APIErrorCodes_Enum.CorruptFileTransfer;
			break;
		case APIErrorCodes_Enum.FileAlreadyExists:
			apiErrorCode_ = APIErrorCodes_Enum.FileAlreadyExists;
			break;
		case APIErrorCodes_Enum.LicenseRestrictionExceeded:
			apiErrorCode_ = APIErrorCodes_Enum.LicenseRestrictionExceeded;
			break;
		case APIErrorCodes_Enum.InvalidLicense:
			apiErrorCode_ = APIErrorCodes_Enum.InvalidLicense;
			break;
		case APIErrorCodes_Enum.DependecyConflict:
			apiErrorCode_ = APIErrorCodes_Enum.DependecyConflict;
			break;
		case APIErrorCodes_Enum.SystemTemporarilyUnavailable:
			apiErrorCode_ = APIErrorCodes_Enum.SystemTemporarilyUnavailable;
			break;
		default:
			return false;
		}
		return true;
	}

	public APIException(string message, APIErrorCodes_Enum apiErrorCode_)
		: base(message)
	{
		m_APIErrorCode = apiErrorCode_;
	}

	public APIException(XmlDocument originalDocument_, string message, APIErrorCodes_Enum apiErrorCode_)
		: base(message)
	{
		m_APIErrorCode = apiErrorCode_;
		m_originalDocument = originalDocument_;
		OriginalDocument = originalDocument_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Assignee
using Moraware.JobTrackerAPI5;

public class Assignee : JTObject
{
	internal enum AssigneeConditionalFieldUpdateFlags_Enum
	{
		cfufAssigneeName = 1,
		cfufDescription = 2,
		cfufIsInactive = 4,
		cfufPostUltimate_Assignee = 8,
		cfufDisplayColor = 0x10
	}

	private string _assigneeName;

	private string _description;

	private bool _isInactive;

	private string _displayColor;

	internal bool ModifiedDescription => base.UpdateFlags.AreFlagsSet(2);

	internal bool ModifiedIsInactive => base.UpdateFlags.AreFlagsSet(4);

	internal bool ModifiedDisplayColor => base.UpdateFlags.AreFlagsSet(16);

	public string Description
	{
		get
		{
			return _description;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_description = value;
		}
	}

	public bool IsInactive
	{
		get
		{
			return _isInactive;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_isInactive = value;
		}
	}

	public string DisplayColor
	{
		get
		{
			return _displayColor;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(16);
			_displayColor = value;
		}
	}

	public int SeqNum { get; internal set; }

	public int AssigneeId { get; internal set; }

	public string AssigneeName
	{
		get
		{
			return _assigneeName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_assigneeName = value;
		}
	}

	internal bool ModifiedAssigneeName => base.UpdateFlags.AreFlagsSet(1);

	public Assignee(int assigneeId_)
	{
		AssigneeId = assigneeId_;
	}

	public Assignee(string assigneeName_)
	{
		AssigneeName = assigneeName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AssigneeContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class AssigneeContainer : IEnumerable<Assignee>, IEnumerable
{
	private Dictionary<int, Assignee> _mapById;

	private List<Assignee> _list = new List<Assignee>();

	private bool m_modified;

	internal bool Modified
	{
		get
		{
			return m_modified;
		}
		set
		{
			m_modified = value;
		}
	}

	internal Dictionary<int, Assignee> MapById
	{
		get
		{
			if (_mapById == null)
			{
				_mapById = new Dictionary<int, Assignee>();
				foreach (Assignee item in _list)
				{
					_mapById.Add(item.AssigneeId, item);
				}
			}
			return _mapById;
		}
	}

	internal void Clear()
	{
		_list.Clear();
		if (_mapById != null)
		{
			_mapById = null;
		}
	}

	internal void ClearUpdateFlags()
	{
		Modified = false;
		using IEnumerator<Assignee> enumerator = GetEnumerator();
		while (enumerator.MoveNext())
		{
			enumerator.Current.ClearUpdateFlags();
		}
	}

	public Assignee ItemAt(int zeroBasedIndex_)
	{
		return _list[zeroBasedIndex_];
	}

	public Assignee Item(int id_)
	{
		Assignee assignee = null;
		if (MapById.ContainsKey(id_))
		{
			return MapById[id_];
		}
		return null;
	}

	public Assignee Item(string name_, bool exceptionIfNotThere_ = false)
	{
		Assignee assignee = null;
		using (IEnumerator<Assignee> enumerator = GetEnumerator())
		{
			while (enumerator.MoveNext())
			{
				Assignee current = enumerator.Current;
				if (name_ == current.AssigneeName)
				{
					return current;
				}
			}
		}
		if (exceptionIfNotThere_)
		{
			throw new APIException(null, "No such item (name=\"" + name_ + "\").", APIException.APIErrorCodes_Enum.NonExistentObject);
		}
		return null;
	}

	internal Assignee Add(Assignee t_)
	{
		if (_mapById != null)
		{
			_mapById.Add(t_.AssigneeId, t_);
		}
		_list.Add(t_);
		Modified = true;
		return t_;
	}

	public bool ContainsItemWithId(int id_)
	{
		return MapById.ContainsKey(id_);
	}

	public int Count()
	{
		return _list.Count;
	}

	public IEnumerator<Assignee> GetEnumerator()
	{
		return _list.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}

	public Assignee AddAssignee(int assigneeId_)
	{
		return Add(new Assignee(assigneeId_));
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.AttachedFile
using Moraware.JobTrackerAPI5;

public class AttachedFile : HasCustomFieldValues
{
	internal enum AttachedFileConditionalFieldUpdateFlags_Enum
	{
		cfufAttachedFileName = 1,
		cfufDescription = 2,
		cfufPostUltimate_AttachedFile = 4
	}

	private string _description;

	private int _parentObjectId;

	private string _attachedFileName;

	internal bool ModifiedDescription => base.UpdateFlags.AreAnyFlagsSet(2);

	public string Description
	{
		get
		{
			return _description;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_description = value;
		}
	}

	public int? Size { get; }

	internal int ParentObjectId
	{
		get
		{
			return _parentObjectId;
		}
		set
		{
			_parentObjectId = value;
		}
	}

	public int AttachedFileId { get; internal set; }

	public string AttachedFileName
	{
		get
		{
			return _attachedFileName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_attachedFileName = value;
		}
	}

	internal bool ModifiedAttachedFileName => base.UpdateFlags.AreFlagsSet(1);

	internal AttachedFile(int parentObjectId_, string name_)
	{
		_attachedFileName = name_;
		ParentObjectId = parentObjectId_;
	}

	internal AttachedFile(int id_, int parentObjectId_, string name_, string description_, int? size_)
	{
		AttachedFileId = id_;
		_attachedFileName = name_;
		ParentObjectId = parentObjectId_;
		Description = description_;
		Size = size_;
	}

	internal AttachedFile(int id_)
	{
		AttachedFileId = id_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.BuiltInDateFilter<F>
using Moraware.JobTrackerAPI5;

internal class BuiltInDateFilter<F> : BuiltInFilter<F, DateFilter>
{
	public BuiltInDateFilter(F field_, DateFilter dateFilter_)
		: base(field_, dateFilter_)
	{
	}

	public BuiltInDateFilter<F> Clone()
	{
		return new BuiltInDateFilter<F>(base.Field, (DateFilter)base.Filter.Clone());
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.BuiltInFilter<T_Field,T_Filter>
internal class BuiltInFilter<T_Field, T_Filter>
{
	public T_Filter Filter { get; set; }

	public T_Field Field { get; }

	public BuiltInFilter(T_Field field_, T_Filter filter_)
	{
		Field = field_;
		Filter = filter_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.BuiltInListOfValuesFilter<F>
using Moraware.JobTrackerAPI5;

internal class BuiltInListOfValuesFilter<F> : BuiltInFilter<F, ListOfValuesFilter>
{
	public BuiltInListOfValuesFilter(F field_, ListOfValuesFilter listOfValuesFilter_)
		: base(field_, listOfValuesFilter_)
	{
	}

	public BuiltInListOfValuesFilter<F> Clone()
	{
		return new BuiltInListOfValuesFilter<F>(base.Field, (ListOfValuesFilter)base.Filter.Clone());
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.BuiltInTextFilter<F>
using Moraware.JobTrackerAPI5;

internal class BuiltInTextFilter<F> : BuiltInFilter<F, TextFilter>
{
	public BuiltInTextFilter(F field_, TextFilter textFilter_)
		: base(field_, textFilter_)
	{
	}

	public BuiltInTextFilter<F> Clone()
	{
		return new BuiltInTextFilter<F>(base.Field, (TextFilter)base.Filter.Clone());
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Connection
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;
using System.Xml;
using Moraware.JobTrackerAPI5;
using Moraware.JobTrackerAPI5.DevelopmentAssistance;

public class Connection
{
	private class AccountCustomFieldTypeCreator : ICustomFieldTypeCreator<AccountCustomFieldType>
	{
		public AccountCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			return new AccountCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_);
		}
	}

	private class JobCustomFieldTypeCreator : ICustomFieldTypeCreator<JobCustomFieldType>
	{
		public JobCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			List<int> processes_ = BuildProcessIdList(processesElement_);
			return new JobCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_, processes_);
		}
	}

	private class JobActivityCustomFieldTypeCreator : ICustomFieldTypeCreator<JobActivityCustomFieldType>
	{
		public JobActivityCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			return new JobActivityCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_);
		}
	}

	private class SupplierCustomFieldTypeCreator : ICustomFieldTypeCreator<SupplierCustomFieldType>
	{
		public SupplierCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			return new SupplierCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_);
		}
	}

	private class PurchaseOrderCustomFieldTypeCreator : ICustomFieldTypeCreator<PurchaseOrderCustomFieldType>
	{
		public PurchaseOrderCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			return new PurchaseOrderCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_);
		}
	}

	private class FileCustomFieldTypeCreator : ICustomFieldTypeCreator<FileCustomFieldType>
	{
		public FileCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			return new FileCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_);
		}
	}

	private class QuoteCustomFieldTypeCreator : ICustomFieldTypeCreator<QuoteCustomFieldType>
	{
		public QuoteCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			return new QuoteCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_);
		}
	}

	private class SerialNumberCustomFieldTypeCreator : ICustomFieldTypeCreator<SerialNumberCustomFieldType>
	{
		public SerialNumberCustomFieldType CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_)
		{
			return new SerialNumberCustomFieldType(customFieldTypeId_, customFieldTypeName_, isInactive_, isCustomSort_, customFieldDataType_);
		}
	}

	private interface ICustomFieldTypeCreator<T> where T : CustomFieldType
	{
		T CreateCustomField(int customFieldTypeId_, string customFieldTypeName_, bool isInactive_, bool isCustomSort_, string customFieldDataType_, XmlElement processesElement_);
	}

	private enum JobActivityCreationType_Enum
	{
		jactNoSeries,
		jactNewSeries,
		jactExistingSeries
	}

	private enum JobActivityUpdateType_Enum
	{
		jautNoSeriesChanges,
		jautRemoveFromSeries,
		jautNewSeries,
		jautExistingSeries,
		jautExtendSeries
	}

	public enum GetJobForm_FieldInclusionType_Enum
	{
		NoFields,
		ExcludeEmptyFields,
		AllFields
	}

	private bool m_includeStackTraceInDescription;

	private string _applicationName;

	private string _jobTrackerAPIVersion;

	private string _dotNetVersion;

	private const string DEFAULT_API_VERSION = "5";

	private static int? DEFAULT_PRERELEASE_API_VERSION;

	public const int JobProcessId = 1;

	private Dictionary<string, string> m_acceptedRequestContentEncodings = new Dictionary<string, string>();

	public bool AutoRefreshOnTimeout { get; set; } = true;

	public string ApplicationName
	{
		get
		{
			return _applicationName;
		}
		set
		{
			if (value == null)
			{
				value = "";
			}
			_applicationName = value;
		}
	}

	public bool IncludeStackTraceInDescription
	{
		get
		{
			return m_includeStackTraceInDescription;
		}
		set
		{
			m_includeStackTraceInDescription = value;
		}
	}

	public string UserName { get; set; }

	public string Password { private get; set; }

	public string Url { get; set; } = "";

	internal string SessionId { get; private set; } = "";

	public bool Connected => SessionId.Length > 0;

	public ICommandTracer CommandTracer { get; set; }

	public bool CompressRequests { get; set; } = true;

	public bool CompressResponses { get; set; }

	public List<Account> GetAccounts(IEnumerable<int> accountIds_)
	{
		return GetAccountsByIdOrName(includeCustomFields_: true, accountIds_);
	}

	public List<Account> GetAccounts(string accountName_)
	{
		return GetAccountsByIdOrName(includeCustomFields_: true, null, accountName_);
	}

	public List<Account> GetAccounts(AccountFilter accountFilter_, PagingOptions pagingOptions_)
	{
		List<Account> list = new List<Account>();
		accountFilter_ = accountFilter_ ?? new AccountFilter();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountQuery");
		XmlElement filterElement_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		AppendViewFilterIfNecessary(filterElement_, accountFilter_.ViewId);
		AppendNecessaryCustomFilters(filterElement_, accountFilter_.CustomFieldFilters);
		AppendAccountStatusFilterIfNecessary(filterElement_, accountFilter_.AccountStatusFilters);
		AppendBuiltInTextFilters(filterElement_, accountFilter_.TextFilters);
		AppendBuiltInListOfValuesFilters(filterElement_, accountFilter_.ListOfValuesFilters);
		AppendPagingSpec(xmlElement, pagingOptions_.FirstRecord, pagingOptions_.PageSize);
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		AddObjectCustomFieldIncludeElements(xmlElement2, "account");
		modInternalXMLHelperFunctions.AppendElements(xmlElement2, new string[6] { "name", "accountingId", "notes", "isInactive", "totalRecords", "createSeparateAddressForJob" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "salesperson"), "name");
		AppendAddressInclude(xmlElement2);
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "defaultJobTemplate"), "name");
		XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("Account names query", xmlElement.OwnerDocument);
		if (pagingOptions_.TotalRecords.HasValue)
		{
			pagingOptions_.TotalRecords = Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(xmlDocument.DocumentElement, "accountQuery").GetAttribute("totalRecords"));
		}
		foreach (XmlElement item in xmlDocument.DocumentElement.SelectNodes("accountQuery/account"))
		{
			list.Add(GetAccountFromAccountElement(item));
		}
		return list;
	}

	private List<Account> GetAccountsByIdOrName(bool includeCustomFields_, IEnumerable<int> accountIds_ = null, string accountName_ = null)
	{
		List<Account> list = new List<Account>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountQuery");
		if (accountName_ == null)
		{
			accountName_ = "";
		}
		if (accountName_.Length > 0)
		{
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "name"), "searchText");
			xmlElement2.SetAttribute("exact", "1");
			xmlElement2.InnerText = accountName_;
		}
		else
		{
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in accountIds_)
			{
				ValidatePositiveId(item, "Account", "Account");
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "account", item);
			}
		}
		XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		if (includeCustomFields_)
		{
			AddObjectCustomFieldIncludeElements(xmlElement3, "account");
		}
		modInternalXMLHelperFunctions.AppendElements(xmlElement3, new string[5] { "name", "accountingId", "notes", "isInactive", "createSeparateAddressForJob" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "salesperson"), "name");
		AppendAddressInclude(xmlElement3);
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "defaultJobTemplate"), "name");
		foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Accounts query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("accountQuery/account"))
		{
			list.Add(GetAccountFromAccountElement(item2));
		}
		return list;
	}

	private Account GetAccountFromAccountElement(XmlElement accountElement_)
	{
		int accountId_ = int.Parse(accountElement_.GetAttribute("id"));
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(accountElement_, "name");
		Account account = new Account(accountId_)
		{
			AccountName = textOfChildIfThere,
			Address = GetAddressFromAddressElement(modInternalXMLHelperFunctions.GetChildElementIfThere(accountElement_, "address")),
			Notes = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(accountElement_, "notes")),
			AccountingId = modInternalXMLHelperFunctions.GetTextOfChildIfThere(accountElement_, "accountingId"),
			IsInactive = GetBooleanFromAttribute(accountElement_, "isInactive"),
			CreateSeparateAddressForJob = GetBooleanFromAttribute(accountElement_, "createSeparateAddressForJob"),
			CustomFieldValues = GetCustomFieldValuesForObject(accountElement_)
		};
		Salesperson salespersonFromSalespersonElement = GetSalespersonFromSalespersonElement(modInternalXMLHelperFunctions.GetChildElementIfThere(accountElement_, "salesperson"));
		if (salespersonFromSalespersonElement == null)
		{
			account.SalespersonId = null;
		}
		else
		{
			account.SetSalesperson(salespersonFromSalespersonElement.SalespersonId, salespersonFromSalespersonElement.SalespersonName);
		}
		foreach (XmlElement item in accountElement_.SelectNodes("defaultJobTemplate"))
		{
			int id_ = int.Parse(item.GetAttribute("id"));
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "name");
			JobTemplate value = new JobTemplate(id_, textOfChildIfThere2);
			int processId_ = int.Parse(item.GetAttribute("processId"));
			account.SetDefaultJobTemplate(processId_, value);
		}
		account.ClearUpdateFlags();
		return account;
	}

	public void UpdateAccount(Account account_, bool allowDuplicates_ = false)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountUpdate");
		if (allowDuplicates_)
		{
			modInternalXMLHelperFunctions.AppendElement(xmlElement, "allowDuplicateAccount");
		}
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "account");
		xmlElement2.SetAttribute("id", account_.AccountId.ToString());
		UpdateElementForAccountUpdateOrCreate(xmlElement2, account_, null, create_: false);
		ExecuteAndIfNecessaryTraceCommand("Account Update", xmlElement.OwnerDocument);
		account_.ClearUpdateFlags();
	}

	public int CreateAccount(Account account_, IEnumerable<AccountContact> contacts_ = null, bool allowDuplicates_ = false)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountCreate");
		if (allowDuplicates_)
		{
			modInternalXMLHelperFunctions.AppendElement(xmlElement, "allowDuplicateAccount");
		}
		UpdateElementForAccountUpdateOrCreate(xmlElement, account_, contacts_, create_: true);
		XmlElement xmlElement2 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Account Create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("accountCreate/account");
		account_.AccountId = int.Parse(xmlElement2.GetAttribute("id"));
		account_.ClearUpdateFlags();
		if (contacts_ != null)
		{
			int num = 0;
			foreach (AccountContact item in contacts_)
			{
				XmlElement xmlElement3 = (XmlElement)xmlElement2.SelectSingleNode($"accountContacts/accountContact[@requestId='{num}']");
				if (xmlElement3 != null)
				{
					item.AccountId = account_.AccountId;
					item.ContactId = int.Parse(xmlElement3.GetAttribute("id"));
				}
				num++;
			}
		}
		return account_.AccountId;
	}

	private void UpdateElementForAccountUpdateOrCreate(XmlElement parentElement_, Account account_, IEnumerable<AccountContact> contacts_, bool create_)
	{
		if (account_.ModifiedAccountName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentElement_, "name", account_.AccountName, includeEmptyTextElements_: true);
		}
		if (account_.ModifiedIsInactive)
		{
			parentElement_.SetAttribute("isInactive", account_.IsInactive ? "1" : "0");
		}
		if (account_.ModifiedCreateSeparateAddressForJob)
		{
			parentElement_.SetAttribute("createSeparateAddressForJob", account_.CreateSeparateAddressForJob ? "1" : "0");
		}
		if (account_.ModifiedAccountingId)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentElement_, "accountingId", account_.AccountingId, !create_);
		}
		if (account_.ModifiedNotes)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentElement_, "notes", account_.Notes, !create_);
		}
		if (account_.ModifiedAddress)
		{
			AppendAddressNodeIfNecessary(parentElement_, account_.Address, "address", !create_);
		}
		if (contacts_ != null)
		{
			int num = 0;
			XmlElement parentElement_2 = modInternalXMLHelperFunctions.AppendElement(parentElement_, "accountContacts");
			foreach (AccountContact item in contacts_)
			{
				Address address = item.Address;
				if (address == null)
				{
					address = new Address();
				}
				AppendAddressNodeIfNecessary(parentElement_2, address, "accountContact", includeEmptyAddressFields_: false).SetAttribute("requestId", $"{num}");
				num++;
			}
		}
		if (account_.ModifiedSalesperson)
		{
			XmlElement xmlElement = modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentElement_, "salesperson", account_.SalespersonName, includeEmptyTextElements_: true);
			if (account_.SalespersonId.HasValue)
			{
				xmlElement.SetAttribute("id", $"{account_.SalespersonId}");
			}
		}
		AppendElementWithIdForCreateOrUpdateIfNecessary(parentElement_, account_.DefaultJobTemplates, create_);
		AddCustomFieldsUpdateOrCreationElement(parentElement_, account_.CustomFieldValues, "account");
	}

	public void DeleteAccount(int accountId_)
	{
		XmlElement xmlElement = CreateCommandDocument("accountDelete");
		ValidateConnected();
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "account", accountId_);
		ExecuteAndIfNecessaryTraceCommand("Account delete", xmlElement.OwnerDocument);
	}

	public List<AccountContact> GetAccountContacts(int accountId_)
	{
		return GetAccountContactOrContacts(null, accountId_);
	}

	public AccountContact GetAccountContact(int accountContactId_)
	{
		List<AccountContact> accountContactOrContacts = GetAccountContactOrContacts(accountContactId_, null);
		if (accountContactOrContacts.Count > 0)
		{
			return accountContactOrContacts[0];
		}
		return null;
	}

	internal List<AccountContact> GetAccountContactOrContacts(int? accountContactId_, int? accountId_)
	{
		List<AccountContact> list = new List<AccountContact>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountContactQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (accountId_.HasValue)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "account", accountId_.Value);
		}
		else
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "accountContact", $"{accountContactId_}");
		}
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), AddressIncludeFields());
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Account (contact) query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("accountContactQuery/accountContact"))
		{
			Address addressFromAddressElement = GetAddressFromAddressElement(item);
			list.Add(new AccountContact(int.Parse(item.GetAttribute("accountId")), int.Parse(item.GetAttribute("id")), addressFromAddressElement));
		}
		return list;
	}

	public void DeleteAccountContacts(IEnumerable<int> contactIds_)
	{
		DeleteByIds(contactIds_, "accountContact", "Account Contact");
	}

	public void DeleteAccountContact(int contactId_)
	{
		DeleteAccountContacts(new int[1] { contactId_ });
	}

	public Account GetAccount(int accountId_)
	{
		List<Account> accountsByIdOrName = GetAccountsByIdOrName(includeCustomFields_: true, new int[1] { accountId_ });
		if (accountsByIdOrName.Count > 0)
		{
			return accountsByIdOrName[0];
		}
		return null;
	}

	public void UpdateAccountContact(AccountContact accountContact_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountContactUpdate");
		XmlElement xmlElement2 = AppendAddressNodeIfNecessary(xmlElement, accountContact_.Address, "accountContact", includeEmptyAddressFields_: true);
		xmlElement2.SetAttribute("id", accountContact_.ContactId.ToString());
		xmlElement2.SetAttribute("accountId", accountContact_.AccountId.ToString());
		ExecuteAndIfNecessaryTraceCommand("Account Contact update", xmlElement.OwnerDocument);
		accountContact_.ClearUpdateFlags();
	}

	public int CreateAccountContact(AccountContact accountContact_)
	{
		ValidateConnected();
		if (accountContact_.AccountId == 0)
		{
			throw new Exception("Trying to create an account contact without specifying the parent account!  (AccountId=0)");
		}
		XmlElement xmlElement = CreateCommandDocument("accountContactCreate");
		AppendAddressNodeIfNecessary(xmlElement, accountContact_.Address, "accountContact", includeEmptyAddressFields_: true).SetAttribute("accountId", accountContact_.AccountId.ToString());
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(ExecuteAndIfNecessaryTraceCommand("Account Contact update", xmlElement.OwnerDocument).DocumentElement, "accountContactCreate/accountContact");
		accountContact_.ContactId = int.Parse(childElementIfThere.GetAttribute("id"));
		accountContact_.ClearUpdateFlags();
		return accountContact_.ContactId;
	}

	public void UpdateAccountPriceList(AccountPriceList accountPriceList_)
	{
		CreateOrUpdateAccountPriceList(accountPriceList_, create_: false);
	}

	public void CreateAccountPriceList(AccountPriceList accountPriceList_)
	{
		CreateOrUpdateAccountPriceList(accountPriceList_, create_: true);
	}

	private void CreateOrUpdateAccountPriceList(AccountPriceList accountPriceList_, bool create_)
	{
		ValidateConnected();
		string text = (create_ ? "Create" : "Update").ToString();
		XmlElement xmlElement = CreateCommandDocument($"accountPriceList{text}");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "accountPriceList");
		xmlElement2.SetAttribute("accountId", accountPriceList_.AccountId.ToString());
		xmlElement2.SetAttribute("priceListId", accountPriceList_.PriceList.PriceListId.ToString());
		if (accountPriceList_.ModifiedDiscountPercent)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "discountPercent", accountPriceList_.DiscountPercent, includeEmptyTextElements_: true);
		}
		if (accountPriceList_.ModifiedTaxPercent)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "taxPercent", accountPriceList_.TaxPercent, includeEmptyTextElements_: true);
		}
		if (accountPriceList_.ModifiedIsInactive)
		{
			xmlElement2.SetAttribute("isInactive", (accountPriceList_.IsInactive ? "1" : "0").ToString());
		}
		ExecuteAndIfNecessaryTraceCommand($"Account Price List {text.ToLower()}", xmlElement.OwnerDocument);
		accountPriceList_.ClearUpdateFlags();
	}

	public void DeleteAccountPriceList(int accountId_, int priceListId_)
	{
		DeleteAccountPriceList(new AccountPriceList(accountId_, null, new PriceList(priceListId_, null, null, isInactive_: false)));
	}

	public void DeleteAccountPriceList(AccountPriceList accountPriceList_)
	{
		DeleteAccountPriceLists(new AccountPriceList[1] { accountPriceList_ });
	}

	public void DeleteAccountPriceLists(IEnumerable<AccountPriceList> accountPriceLists_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountPriceListDelete");
		new Dictionary<int, XmlElement>();
		foreach (AccountPriceList item in accountPriceLists_)
		{
			if (item.PriceList != null)
			{
				XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "accountPriceList");
				xmlElement2.SetAttribute("accountId", item.AccountId.ToString());
				xmlElement2.SetAttribute("priceListId", item.PriceList.PriceListId.ToString());
			}
		}
		ExecuteAndIfNecessaryTraceCommand("Account Price List delete", xmlElement.OwnerDocument);
	}

	public AccountPriceList GetAccountPriceList(int accountId_, int priceListId_)
	{
		List<AccountPriceList> accountPriceLists = GetAccountPriceLists(accountId_, priceListId_);
		if (accountPriceLists.Count == 0)
		{
			return null;
		}
		return accountPriceLists[0];
	}

	public List<AccountPriceList> GetAccountPriceLists(int accountId_)
	{
		return GetAccountPriceLists(accountId_, null);
	}

	internal List<AccountPriceList> GetAccountPriceLists(int accountId_, int? priceListId_)
	{
		List<AccountPriceList> list = null;
		list = new List<AccountPriceList>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("accountPriceListQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(parentNode_, "priceList"), new string[4] { "name", "isInactive", "seqNum", "defaultTaxPercent" });
		modInternalXMLHelperFunctions.AppendElements(parentNode_, new string[4] { "seqNum", "isInactive", "taxPercent", "discountPercent" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_, "account"), "name");
		XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (priceListId_.HasValue)
		{
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(parentNode_2, "accountPriceList");
			xmlElement2.SetAttribute("priceListId", priceListId_.ToString());
			xmlElement2.SetAttribute("accountId", accountId_.ToString());
		}
		else
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_2, "account", accountId_);
		}
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Account Price List query", xmlElement.OwnerDocument).DocumentElement.SelectNodes($"accountPriceListQuery/accountPriceList[@accountId='{accountId_}']"))
		{
			XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(item, "priceList");
			bool booleanFromAttribute = GetBooleanFromAttribute(childElementIfThere, "isInactive");
			bool booleanFromAttribute2 = GetBooleanFromAttribute(item, "isInactive");
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "defaultTaxPercent");
			modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "seqNum");
			PriceList priceList_ = new PriceList(int.Parse(childElementIfThere.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name"), ParseDecimalIfThere(textOfChildIfThere), booleanFromAttribute);
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "taxPercent");
			string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "discountPercent");
			AccountPriceList accountPriceList = new AccountPriceList(accountId_, modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "account/name"), priceList_)
			{
				TaxPercent = ParseDecimalIfThere(textOfChildIfThere2),
				DiscountPercent = ParseDecimalIfThere(textOfChildIfThere3),
				IsInactive = booleanFromAttribute2
			};
			accountPriceList.ClearUpdateFlags();
			list.Add(accountPriceList);
		}
		return list;
	}

	private Address GetAddressFromAddressElement(XmlElement addressElement_)
	{
		Address address = null;
		if (addressElement_ == null)
		{
			address = null;
		}
		else
		{
			address = new Address(modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "contactName"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "addressLine1"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "addressLine2"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "city"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "state"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "zip"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "country"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "phone"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "phone2"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "cell"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "fax"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "email"), CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(addressElement_, "notes")));
			address.ClearUpdateFlags();
		}
		return address;
	}

	private string[] AddressIncludeFields()
	{
		return new string[13]
		{
			"contactName", "addressLine1", "addressLine2", "city", "state", "zip", "country", "phone", "phone2", "cell",
			"fax", "email", "notes"
		};
	}

	private void AppendAddressInclude(XmlElement includeElement_)
	{
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(includeElement_, "address"), AddressIncludeFields());
	}

	private XmlElement AppendAddressNodeIfNecessary(XmlElement parentElement_, Address address_, string addressElementName_, bool includeEmptyAddressFields_)
	{
		XmlElement xmlElement = null;
		if (address_ == null)
		{
			xmlElement = null;
		}
		else if (address_.Modified || includeEmptyAddressFields_)
		{
			xmlElement = modInternalXMLHelperFunctions.AppendElement(parentElement_, addressElementName_);
			if (address_.ModifiedContactName)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "contactName", address_.ContactName, includeEmptyAddressFields_);
			}
			if (address_.ModifiedAddressLine1)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "addressLine1", address_.AddressLine1, includeEmptyAddressFields_);
			}
			if (address_.ModifiedAddressLine2)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "addressLine2", address_.AddressLine2, includeEmptyAddressFields_);
			}
			if (address_.ModifiedCity)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "city", address_.City, includeEmptyAddressFields_);
			}
			if (address_.ModifiedState)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "state", address_.State, includeEmptyAddressFields_);
			}
			if (address_.ModifiedZip)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "zip", address_.Zip, includeEmptyAddressFields_);
			}
			if (address_.ModifiedCountry)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "country", address_.Country, includeEmptyAddressFields_);
			}
			if (address_.ModifiedPhone)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "phone", address_.Phone, includeEmptyAddressFields_);
			}
			if (address_.ModifiedPhone2)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "phone2", address_.Phone2, includeEmptyAddressFields_);
			}
			if (address_.ModifiedFax)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "fax", address_.Fax, includeEmptyAddressFields_);
			}
			if (address_.ModifiedNotes)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "notes", address_.Notes, includeEmptyAddressFields_);
			}
			if (address_.ModifiedCell)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "cell", address_.Cell, includeEmptyAddressFields_);
			}
			if (address_.ModifiedEmail)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "email", address_.Email, includeEmptyAddressFields_);
			}
		}
		else
		{
			xmlElement = null;
		}
		return xmlElement;
	}

	public Assignee GetAssignee(int assigneeId_)
	{
		List<Assignee> assignees = GetAssignees(new int[1] { assigneeId_ });
		if (assignees.Count == 0)
		{
			return null;
		}
		return assignees[0];
	}

	public List<Assignee> GetAssignees()
	{
		return GetAssignees(null);
	}

	private List<Assignee> GetAssignees(IEnumerable<int> assigneeIds_)
	{
		List<Assignee> list = new List<Assignee>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("assigneeQuery");
		if (assigneeIds_ != null)
		{
			flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in assigneeIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "assignee", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[5] { "name", "seqNum", "displayColor", "isInactive", "description" });
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Assignee query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("assigneeQuery/assignee"))
			{
				list.Add(GetAssigneeFromAssigneeElement(item2));
			}
		}
		return list;
	}

	private Assignee GetAssigneeFromAssigneeElement(XmlElement assigneeElement_)
	{
		Assignee assignee = new Assignee(int.Parse(assigneeElement_.GetAttribute("id")));
		assignee.AssigneeName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(assigneeElement_, "name");
		assignee.Description = modInternalXMLHelperFunctions.GetTextOfChildIfThere(assigneeElement_, "description");
		assignee.IsInactive = GetBooleanFromAttribute(assigneeElement_, "isInactive");
		assignee.DisplayColor = modInternalXMLHelperFunctions.GetTextOfChildIfThere(assigneeElement_, "displayColor");
		assignee.SeqNum = int.Parse(assigneeElement_.GetAttribute("seqNum"));
		assignee.ClearUpdateFlags();
		return assignee;
	}

	public void DeleteAssignee(int assigneeId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("assigneeDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "assignee", assigneeId_);
		ExecuteAndIfNecessaryTraceCommand("Assignee delete", xmlElement.OwnerDocument);
	}

	public int CreateAssignee(Assignee assignee_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("assigneeCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "assignee");
		if (assignee_.IsInactive)
		{
			xmlElement2.SetAttribute("isInactive", "1");
		}
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", assignee_.AssigneeName, includeEmptyTextElements_: true);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "description", assignee_.Description, includeEmptyTextElements_: true);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "displayColor", assignee_.DisplayColor);
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Assignee create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("assigneeCreate/assignee");
		assignee_.AssigneeId = int.Parse(xmlElement3.GetAttribute("id"));
		assignee_.ClearUpdateFlags();
		return assignee_.AssigneeId;
	}

	public void UpdateAssignee(Assignee assignee_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("assigneeUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "assignee", assignee_.AssigneeId);
		if (assignee_.ModifiedIsInactive)
		{
			xmlElement2.SetAttribute("isInactive", $"{(assignee_.IsInactive ? 1 : 0)}");
		}
		if (assignee_.ModifiedAssigneeName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", assignee_.AssigneeName, includeEmptyTextElements_: true);
		}
		if (assignee_.ModifiedDescription)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "description", assignee_.Description, includeEmptyTextElements_: true);
		}
		if (assignee_.ModifiedDisplayColor)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "displayColor", assignee_.DisplayColor, includeEmptyTextElements_: true);
		}
		ExecuteAndIfNecessaryTraceCommand("Assignee update", xmlElement.OwnerDocument);
		assignee_.ClearUpdateFlags();
	}

	private void AppendAssigneesForCreateOrUpdate(XmlNode parent_, AssigneeContainer assignees_)
	{
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(parent_, "assignees");
		if (assignees_ == null)
		{
			return;
		}
		foreach (Assignee item in assignees_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "assignee", item.AssigneeId);
		}
	}

	public void ReorderAssignees(IEnumerable<int> assigneeIds_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("assigneeReorder");
		foreach (int item in assigneeIds_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "assignee", item);
		}
		if (xmlElement.SelectSingleNode("*") != null)
		{
			ExecuteAndIfNecessaryTraceCommand("Assignee reorder", xmlElement.OwnerDocument);
		}
	}

	private void AddObjectCustomFieldIncludeElements(XmlElement parentIncludeElement_, string prefix_)
	{
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(parentIncludeElement_, $"{prefix_}CustomField"), new string[3] { "name", "dataType", "allFieldTypes" });
	}

	public List<CustomLOVFieldValue> GetCustomLOVFieldValues(int customFieldId_)
	{
		List<CustomLOVFieldValue> list = null;
		ValidateConnected();
		list = new List<CustomLOVFieldValue>();
		XmlElement xmlElement = CreateCommandDocument("customLOVFieldValueQuery");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "customFieldType").SetAttribute("id", customFieldId_.ToString());
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[4] { "value", "isInactive", "displayColor", "seqNum" });
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Custom LOV field query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("customLOVFieldValueQuery/customFieldType/customFieldValue"))
		{
			int id_ = int.Parse(item.GetAttribute("id"));
			bool isInactive_ = "1" == item.GetAttribute("isInactive");
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "value");
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "displayColor");
			int? seqNum_ = null;
			if (item.HasAttribute("seqNum"))
			{
				seqNum_ = int.Parse(item.GetAttribute("seqNum"));
			}
			list.Add(new CustomLOVFieldValue(id_, textOfChildIfThere, isInactive_, textOfChildIfThere2, seqNum_));
		}
		return list;
	}

	public List<AccountCustomFieldType> GetCustomAccountFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("account", includeInactive_, new AccountCustomFieldTypeCreator());
	}

	public List<JobCustomFieldType> GetCustomJobFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("job", includeInactive_, new JobCustomFieldTypeCreator());
	}

	public List<JobCustomFieldType> GetCustomJobFieldTypes(bool includeInactive_, int processId_)
	{
		return GetCustomFieldTypes("job", includeInactive_, new JobCustomFieldTypeCreator(), new int[1] { processId_ });
	}

	internal List<QuoteCustomFieldType> GetCustomQuoteFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("quote", includeInactive_, new QuoteCustomFieldTypeCreator());
	}

	public List<JobActivityCustomFieldType> GetCustomJobActivityFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("jobActivity", includeInactive_, new JobActivityCustomFieldTypeCreator());
	}

	public List<PurchaseOrderCustomFieldType> GetCustomPurchaseOrderFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("purchaseOrder", includeInactive_, new PurchaseOrderCustomFieldTypeCreator());
	}

	public List<FileCustomFieldType> GetCustomFileFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("file", includeInactive_, new FileCustomFieldTypeCreator());
	}

	public List<SerialNumberCustomFieldType> GetCustomSerialNumberFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("serialNumber", includeInactive_, new SerialNumberCustomFieldTypeCreator());
	}

	public List<SupplierCustomFieldType> GetCustomSupplierFieldTypes(bool includeInactive_)
	{
		return GetCustomFieldTypes("supplier", includeInactive_, new SupplierCustomFieldTypeCreator());
	}

	public void ReorderCustomLOVFieldValues(int customFieldTypeId_, IEnumerable<int> fieldValueIds_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("customLOVFieldValueReorder");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "customFieldType", customFieldTypeId_);
		foreach (int item in fieldValueIds_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "customFieldValue", item);
		}
		if (xmlElement.SelectSingleNode("*") != null)
		{
			ExecuteAndIfNecessaryTraceCommand("Custom List of Values field reorder", xmlElement.OwnerDocument);
		}
	}

	private void AddCustomFieldsUpdateOrCreationElement(XmlElement parentElement_, CustomFieldValueContainer customFieldValues_, string prefix_)
	{
		if (customFieldValues_ == null || !customFieldValues_.Modified)
		{
			return;
		}
		XmlElement xmlElement = null;
		foreach (CustomFieldValue item in customFieldValues_)
		{
			if (item.ModifiedFieldValue())
			{
				if (xmlElement == null)
				{
					xmlElement = modInternalXMLHelperFunctions.AppendElement(parentElement_, $"{prefix_}CustomFields");
				}
				XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendObjectAsTextElement(modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, $"{prefix_}CustomField", item.CustomFieldTypeId), "value", item.FieldValue, includeEmptyTextElements_: true);
				if (item.FieldValueId.HasValue)
				{
					xmlElement2.SetAttribute("id", item.FieldValueId.ToString());
				}
			}
		}
	}

	private List<T> GetCustomFieldTypes<T>(string objectType_, bool includeInactive_, ICustomFieldTypeCreator<T> customFieldTypeCreator_, IEnumerable<int> processIds_ = null) where T : CustomFieldType
	{
		List<T> list = new List<T>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument(objectType_ + "CustomFieldTypeQuery");
		if (processIds_ != null)
		{
			AppendProcessesToFilter(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), processIds_);
		}
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		if (objectType_ == "job")
		{
			modInternalXMLHelperFunctions.AppendElement(parentNode_, "processes");
		}
		modInternalXMLHelperFunctions.AppendElements(parentNode_, new string[5] { "name", "description", "isInactive", "isCustomSort", "dataType" });
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand($"Custom {objectType_} Field Type query", xmlElement.OwnerDocument).DocumentElement.SelectNodes($"{objectType_}CustomFieldTypeQuery/{objectType_}CustomFieldType"))
		{
			bool flag = "1" == item.GetAttribute("isInactive");
			if (includeInactive_ || !flag)
			{
				bool isCustomSort_ = "1" == item.GetAttribute("isCustomSort");
				int customFieldTypeId_ = int.Parse(item.GetAttribute("id"));
				string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "name");
				string attribute = item.GetAttribute("dataType");
				list.Add(customFieldTypeCreator_.CreateCustomField(customFieldTypeId_, textOfChildIfThere, flag, isCustomSort_, attribute, modInternalXMLHelperFunctions.GetChildElementIfThere(item, "processes")));
			}
		}
		return list;
	}

	private CustomFieldValueContainer GetCustomFieldValuesForObject(XmlElement objectElement_)
	{
		CustomFieldValueContainer customFieldValueContainer = null;
		customFieldValueContainer = new CustomFieldValueContainer();
		foreach (XmlElement item in objectElement_.SelectNodes("customField"))
		{
			int customFieldTypeId_ = int.Parse(item.GetAttribute("id"));
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "name");
			string attribute = item.GetAttribute("dataType");
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "text");
			XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(item, "value");
			int? fieldValueId_ = null;
			if (childElementIfThere != null && childElementIfThere.HasAttribute("id"))
			{
				fieldValueId_ = int.Parse(childElementIfThere.GetAttribute("id"));
			}
			string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "value");
			string textOfChildIfThere4 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "number");
			string textOfChildIfThere5 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "date");
			string textOfChildIfThere6 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "url");
			CustomFieldValue customFieldValue = customFieldValueContainer.AddCustomFieldValue(customFieldTypeId_, textOfChildIfThere, attribute);
			string fieldValue_ = CanonicalizeMultiLineTextFromResponse(textOfChildIfThere2 + textOfChildIfThere3 + textOfChildIfThere4 + textOfChildIfThere5 + textOfChildIfThere6);
			customFieldValue.SetFieldIdAndValue(fieldValueId_, fieldValue_);
			customFieldValue.ClearUpdateFlags();
		}
		return customFieldValueContainer;
	}

	public List<JobFile> GetJobFiles(int jobId_, bool includeJobPhases_)
	{
		List<JobFile> list = new List<JobFile>();
		foreach (AttachedFile item in GetFilesOfStandardParentObject(jobId_, "job", includeJobPhases_))
		{
			list.Add((JobFile)item);
		}
		return list;
	}

	public List<AccountFile> GetAccountFiles(int accountId_)
	{
		List<AccountFile> list = new List<AccountFile>();
		foreach (AttachedFile item in GetFilesOfStandardParentObject(accountId_, "account"))
		{
			list.Add((AccountFile)item);
		}
		return list;
	}

	internal List<QuoteFile> GetQuoteFiles(int quoteId_)
	{
		List<QuoteFile> list = new List<QuoteFile>();
		foreach (AttachedFile item in GetFilesOfStandardParentObject(quoteId_, "quote"))
		{
			list.Add((QuoteFile)item);
		}
		return list;
	}

	public List<PurchaseOrderFile> GetPurchaseOrderFiles(int poId_)
	{
		List<PurchaseOrderFile> list = new List<PurchaseOrderFile>();
		foreach (AttachedFile item in GetFilesOfStandardParentObject(poId_, "purchaseOrder"))
		{
			list.Add((PurchaseOrderFile)item);
		}
		return list;
	}

	public List<SupplierFile> GetSupplierFiles(int supplierId_)
	{
		List<SupplierFile> list = new List<SupplierFile>();
		foreach (AttachedFile item in GetFilesOfStandardParentObject(supplierId_, "supplier"))
		{
			list.Add((SupplierFile)item);
		}
		return list;
	}

	public List<SerialNumberFile> GetSerialNumberFiles(int serialNumberId_)
	{
		List<SerialNumberFile> list = new List<SerialNumberFile>();
		foreach (AttachedFile item in GetFilesOfStandardParentObject(serialNumberId_, "serialNumber"))
		{
			list.Add((SerialNumberFile)item);
		}
		return list;
	}

	public JobFile GetJobFile(int fileId_, bool includeJobPhases_)
	{
		return (JobFile)GetFileOfStandardParentObject(fileId_, "job", includeJobPhases_);
	}

	public AccountFile GetAccountFile(int fileId_)
	{
		return (AccountFile)GetFileOfStandardParentObject(fileId_, "account");
	}

	internal QuoteFile GetQuoteFile(int fileId_)
	{
		return (QuoteFile)GetFileOfStandardParentObject(fileId_, "quote");
	}

	public PurchaseOrderFile GetPurchaseOrderFile(int fileId_)
	{
		return (PurchaseOrderFile)GetFileOfStandardParentObject(fileId_, "purchaseOrder");
	}

	public SupplierFile GetSupplierFile(int fileId_)
	{
		return (SupplierFile)GetFileOfStandardParentObject(fileId_, "supplier");
	}

	public SerialNumberFile GetSerialNumberFile(int fileId_)
	{
		return (SerialNumberFile)GetFileOfStandardParentObject(fileId_, "serialNumber");
	}

	public void DeleteJobFile(int fileId_)
	{
		DeleteFile(fileId_, "job");
	}

	public void DeleteAccountFile(int fileId_)
	{
		DeleteFile(fileId_, "account");
	}

	internal void DeleteQuoteFile(int fileId_)
	{
		DeleteFile(fileId_, "quote");
	}

	public void DeletePurchaseOrderFile(int fileId_)
	{
		DeleteFile(fileId_, "purchaseOrder");
	}

	public void DeleteSerialNumberFile(int fileId_)
	{
		DeleteFile(fileId_, "serialNumber");
	}

	public void DeleteSupplierFile(int fileId_)
	{
		DeleteFile(fileId_, "supplier");
	}

	private void DeleteFile(int fileId_, string parentFileTypeName_)
	{
		XmlElement xmlElement = CreateCommandDocument($"{parentFileTypeName_}FileDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "file", fileId_);
		ExecuteAndIfNecessaryTraceCommand($"{parentFileTypeName_} File query", xmlElement.OwnerDocument);
	}

	private List<AttachedFile> GetFilesOfStandardParentObject(int parentObjectId_, string parentFileTypeName_, bool includeJobPhases_ = false)
	{
		List<AttachedFile> list = null;
		list = new List<AttachedFile>();
		XmlElement xmlElement = CreateCommandDocument($"{parentFileTypeName_}FileQuery");
		modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), parentFileTypeName_, parentObjectId_);
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElements(xmlElement2, new string[3] { "name", "description", "size" });
		AddObjectCustomFieldIncludeElements(xmlElement2, "file");
		if (includeJobPhases_)
		{
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobPhase"), "all");
		}
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand($"{parentFileTypeName_} File query", xmlElement.OwnerDocument).DocumentElement.SelectNodes($"{parentFileTypeName_}FileQuery/file"))
		{
			AttachedFile fileOfStandardParentObjectFromElement = GetFileOfStandardParentObjectFromElement(item, parentFileTypeName_);
			list.Add(fileOfStandardParentObjectFromElement);
		}
		return list;
	}

	private AttachedFile GetFileOfStandardParentObject(int fileId_, string parentFileTypeName_, bool includeJobPhases_ = false)
	{
		XmlElement xmlElement = CreateCommandDocument($"{parentFileTypeName_}FileQuery");
		modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "file", fileId_);
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElements(xmlElement2, new string[3] { "name", "description", "size" });
		AddObjectCustomFieldIncludeElements(xmlElement2, "file");
		if (includeJobPhases_)
		{
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobPhase"), "all");
		}
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(ExecuteAndIfNecessaryTraceCommand($"{parentFileTypeName_} File query", xmlElement.OwnerDocument).DocumentElement, $"{parentFileTypeName_}FileQuery/file");
		return GetFileOfStandardParentObjectFromElement(childElementIfThere, parentFileTypeName_);
	}

	private AttachedFile GetFileOfStandardParentObjectFromElement(XmlElement fileElement_, string parentFileTypeName_)
	{
		AttachedFile attachedFile = null;
		if (fileElement_ != null)
		{
			int? size_ = null;
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "size");
			if (textOfChildIfThere.Length > 0)
			{
				size_ = int.Parse(textOfChildIfThere);
			}
			switch (parentFileTypeName_)
			{
			case "job":
			{
				JobFile jobFile = new JobFile(int.Parse(fileElement_.GetAttribute("id")), Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(fileElement_, "job").GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "description"), size_);
				GetJobPhasesIfThere(jobFile.JobPhases, fileElement_, Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(fileElement_, "job").GetAttribute("id")));
				attachedFile = jobFile;
				break;
			}
			case "account":
				attachedFile = new AccountFile(int.Parse(fileElement_.GetAttribute("id")), Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(fileElement_, "account").GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "description"), size_);
				break;
			case "quote":
				attachedFile = new QuoteFile(int.Parse(fileElement_.GetAttribute("id")), Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(fileElement_, "quote").GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "description"), size_);
				break;
			case "purchaseOrder":
				attachedFile = new PurchaseOrderFile(int.Parse(fileElement_.GetAttribute("id")), Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(fileElement_, "purchaseOrder").GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "description"), size_);
				break;
			case "serialNumber":
				attachedFile = new SerialNumberFile(int.Parse(fileElement_.GetAttribute("id")), Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(fileElement_, "serialNumber").GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "description"), size_);
				break;
			case "supplier":
				attachedFile = new SupplierFile(int.Parse(fileElement_.GetAttribute("id")), Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(fileElement_, "supplier").GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(fileElement_, "description"), size_);
				break;
			default:
				throw new Exception("Internal error:  Unsupported standard file, " + $"parent file type name:  \"{parentFileTypeName_}\"");
			}
			attachedFile.CustomFieldValues = GetCustomFieldValuesForObject(fileElement_);
			attachedFile.ClearUpdateFlags();
		}
		return attachedFile;
	}

	private void UpdateFile(AttachedFile attachedFile_, string parentFileTypeName_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument(parentFileTypeName_ + "FileUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "file", attachedFile_.AttachedFileId);
		if (attachedFile_.ModifiedDescription)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "description", attachedFile_.Description, includeEmptyTextElements_: true);
		}
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, attachedFile_.CustomFieldValues, "file");
		if (parentFileTypeName_ == "job" && ((JobFile)attachedFile_).ModifiedJobPhases)
		{
			AppendJobPhasesForCreateOrUpdate(xmlElement2, ((JobFile)attachedFile_).JobPhases, forceIncludeJobPhasesElement_: true);
		}
		ExecuteAndIfNecessaryTraceCommand($"{parentFileTypeName_} File update", xmlElement.OwnerDocument);
		attachedFile_.ClearUpdateFlags();
	}

	public void UploadAccountFile(AccountFile accountFile_, FileInfo fileInfo_, bool overwriteExisting_, IFileTransferMonitor feedback_ = null, bool suppressExceptions_ = false)
	{
		UploadFile(accountFile_, fileInfo_, overwriteExisting_, "account", feedback_, suppressExceptions_);
	}

	public bool DownloadAccountFile(int fileId_, FileInfo targetPath_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false, IFileTransferMonitor feedback_ = null)
	{
		return DownloadFile(fileId_, targetPath_, "account", feedback_, overwriteExistingFile_, suppressExceptions_);
	}

	public void UpdateAccountFile(AccountFile accountFile_)
	{
		UpdateFile(accountFile_, "account");
	}

	public void UploadJobFile(JobFile jobFile_, FileInfo fileInfo_, bool overwriteExisting_, IFileTransferMonitor feedback_ = null, bool suppressExceptions_ = false)
	{
		UploadFile(jobFile_, fileInfo_, overwriteExisting_, "job", feedback_, suppressExceptions_);
	}

	public bool DownloadJobFile(int fileId_, FileInfo targetPath_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false, IFileTransferMonitor feedback_ = null)
	{
		return DownloadFile(fileId_, targetPath_, "job", feedback_, overwriteExistingFile_, suppressExceptions_);
	}

	public void UpdateJobFile(JobFile jobFile_)
	{
		UpdateFile(jobFile_, "job");
	}

	public void UploadPurchaseOrderFile(PurchaseOrderFile purchaseOrderFile_, FileInfo fileInfo_, bool overwriteExisting_, IFileTransferMonitor feedback_ = null, bool suppressExceptions_ = false)
	{
		UploadFile(purchaseOrderFile_, fileInfo_, overwriteExisting_, "purchaseOrder", feedback_, suppressExceptions_);
	}

	public bool DownloadPurchaseOrderFile(int fileId_, FileInfo targetPath_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false, IFileTransferMonitor feedback_ = null)
	{
		return DownloadFile(fileId_, targetPath_, "purchaseOrder", feedback_, overwriteExistingFile_, suppressExceptions_);
	}

	public void UpdatePurchaseOrderFile(PurchaseOrderFile purchaseOrderFile_)
	{
		UpdateFile(purchaseOrderFile_, "purchaseOrder");
	}

	public void UploadSupplierFile(SupplierFile supplierFile_, FileInfo fileInfo_, bool overwriteExisting_, IFileTransferMonitor feedback_ = null, bool suppressExceptions_ = false)
	{
		UploadFile(supplierFile_, fileInfo_, overwriteExisting_, "supplier", feedback_, suppressExceptions_);
	}

	public bool DownloadSupplierFile(int fileId_, FileInfo targetPath_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false, IFileTransferMonitor feedback_ = null)
	{
		return DownloadFile(fileId_, targetPath_, "supplier", feedback_, overwriteExistingFile_, suppressExceptions_);
	}

	public void UpdateSupplierFile(SupplierFile supplierFile_)
	{
		UpdateFile(supplierFile_, "supplier");
	}

	internal void UploadQuoteFile(QuoteFile quoteFile_, FileInfo fileInfo_, bool overwriteExisting_, IFileTransferMonitor feedback_ = null, bool suppressExceptions_ = false)
	{
		UploadFile(quoteFile_, fileInfo_, overwriteExisting_, "quote", feedback_, suppressExceptions_);
	}

	internal bool DownloadQuoteFile(int fileId_, FileInfo targetPath_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false, IFileTransferMonitor feedback_ = null)
	{
		return DownloadFile(fileId_, targetPath_, "quote", feedback_, overwriteExistingFile_, suppressExceptions_);
	}

	internal void UpdateQuoteFile(QuoteFile quoteFile_)
	{
		UpdateFile(quoteFile_, "quote");
	}

	public void UploadSerialNumberFile(SerialNumberFile serialNumberFile_, FileInfo fileInfo_, bool overwriteExisting_, IFileTransferMonitor feedback_ = null, bool suppressExceptions_ = false)
	{
		UploadFile(serialNumberFile_, fileInfo_, overwriteExisting_, "serialNumber", feedback_, suppressExceptions_);
	}

	public bool DownloadSerialNumberFile(int fileId_, FileInfo targetPath_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false, IFileTransferMonitor feedback_ = null)
	{
		return DownloadFile(fileId_, targetPath_, "serialNumber", feedback_, overwriteExistingFile_, suppressExceptions_);
	}

	public void UpdateSerialNumberFile(SerialNumberFile serialNumberFile_)
	{
		UpdateFile(serialNumberFile_, "serialNumber");
	}

	private bool DownloadFile(int fileId_, FileInfo targetPath_, string fileTypePrefix_, IFileTransferMonitor feedback_ = null, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false)
	{
		bool result = false;
		if (suppressExceptions_)
		{
			try
			{
				result = UncaughtDownloadFile(fileId_, targetPath_, fileTypePrefix_, feedback_, overwriteExistingFile_, suppressExceptions_);
			}
			catch (Exception)
			{
			}
		}
		else
		{
			result = UncaughtDownloadFile(fileId_, targetPath_, fileTypePrefix_, feedback_, overwriteExistingFile_, suppressExceptions_);
		}
		return result;
	}

	private bool UncaughtDownloadFile(int fileId_, FileInfo targetPath_, string fileTypePrefix_, IFileTransferMonitor feedback_ = null, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false)
	{
		if (targetPath_.Exists)
		{
			if (!overwriteExistingFile_)
			{
				throw new Exception("File exists!");
			}
			targetPath_.Delete();
		}
		FileInfo fileInfo = new FileInfo(Path.GetTempFileName());
		int num = -1;
		int num2 = 0;
		FileTransferProgressEvent fileTransferProgressEvent = new FileTransferProgressEvent(0, 0);
		bool flag = false;
		try
		{
			using FileStream fileStream = fileInfo.OpenWrite();
			do
			{
				XmlElement xmlElement = CreateCommandDocument($"{fileTypePrefix_}FileDownload");
				xmlElement.SetAttribute("fileId", fileId_.ToString());
				xmlElement.SetAttribute("firstByteOffset", num2.ToString());
				XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("File download", xmlElement.OwnerDocument);
				XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(xmlDocument.DocumentElement, $"{fileTypePrefix_}FileDownload/payloadDescription");
				num = int.Parse(childElementIfThere.GetAttribute("fileSize"));
				int num3 = int.Parse(childElementIfThere.GetAttribute("chunkSize"));
				num2 += num3;
				flag = "1" == childElementIfThere.GetAttribute("finalChunk");
				if (num3 > 0)
				{
					byte[] array = Convert.FromBase64String(modInternalXMLHelperFunctions.GetTextOfChildIfThere(xmlDocument.DocumentElement, $"{fileTypePrefix_}FileDownload/payload/data"));
					if (array.Length != 0)
					{
						fileStream.Write(array, 0, array.Length);
					}
				}
				if (feedback_ != null)
				{
					fileTransferProgressEvent.ExpectedBytes = num;
					fileTransferProgressEvent.BytesSoFar = num2;
					feedback_.UpdateStatus(fileTransferProgressEvent);
				}
			}
			while (!flag && !fileTransferProgressEvent.Halted);
		}
		catch (Exception ex)
		{
			if (feedback_ != null)
			{
				feedback_.UpdateStatus(new FileTransferProgressEvent(num2, num, ex));
				try
				{
					fileInfo.Delete();
				}
				catch (Exception)
				{
				}
			}
			throw ex;
		}
		if (feedback_ != null)
		{
			if (flag)
			{
				feedback_.UpdateStatus(new FileTransferProgressEvent(num2));
			}
			else
			{
				feedback_.UpdateStatus(new FileTransferProgressEvent(num2, num, cancelled_: true));
				fileInfo.Delete();
			}
		}
		if (fileInfo.Exists)
		{
			fileInfo.MoveTo(targetPath_.FullName);
		}
		return flag;
	}

	private void UploadFile(AttachedFile jtFile_, FileInfo fileInfo_, bool overwriteExisting_, string fileTypePrefix_, IFileTransferMonitor feedback_ = null, bool suppressExceptions_ = false)
	{
		int num = 0;
		int num2 = 0;
		try
		{
			XmlElement xmlElement = CreateCommandDocument(fileTypePrefix_ + "FileUpload");
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement, "name", jtFile_.AttachedFileName);
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "description", jtFile_.Description, jtFile_.ModifiedDescription);
			AddCustomFieldsUpdateOrCreationElement(xmlElement, jtFile_.CustomFieldValues, "file");
			if (overwriteExisting_)
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement, "overwrite");
			}
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "payloadDescription");
			if (fileTypePrefix_ == "job")
			{
				JobFile jobFile = (JobFile)jtFile_;
				if (jobFile.ModifiedJobPhases)
				{
					AppendJobPhasesForCreateOrUpdate(xmlElement, jobFile.JobPhases, forceIncludeJobPhasesElement_: true);
				}
			}
			MD5CryptoServiceProvider mD5CryptoServiceProvider = new MD5CryptoServiceProvider();
			StringBuilder stringBuilder = new StringBuilder();
			using (FileStream inputStream = new FileStream(fileInfo_.FullName, FileMode.Open, FileAccess.Read, FileShare.Read, 8192))
			{
				byte[] array = mD5CryptoServiceProvider.ComputeHash(inputStream);
				foreach (byte b in array)
				{
					stringBuilder.Append($"{b:X2}");
				}
			}
			xmlElement2.SetAttribute("fileMD5", stringBuilder.ToString());
			xmlElement2.SetAttribute("fileSize", fileInfo_.Length.ToString());
			xmlElement2.SetAttribute(fileTypePrefix_ + "Id", jtFile_.ParentObjectId.ToString());
			XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("File upload", xmlElement.OwnerDocument);
			XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(xmlDocument.DocumentElement, $"{fileTypePrefix_}FileUpload/options");
			int num3 = int.Parse(childElementIfThere.GetAttribute("tempFileId"));
			int num4 = int.Parse(childElementIfThere.GetAttribute("maxChunkSize"));
			if (num4 > 102400)
			{
				num4 = 102400;
			}
			num2 = (int)fileInfo_.Length;
			using (FileStream fileStream = new FileStream(fileInfo_.FullName, FileMode.Open, FileAccess.Read, FileShare.Read, num4))
			{
				byte[] array2 = new byte[num4];
				num = num2;
				FileTransferProgressEvent fileTransferProgressEvent = new FileTransferProgressEvent(0, num);
				xmlDocument = null;
				do
				{
					int num5 = fileStream.Read(array2, 0, num4);
					num2 -= num5;
					xmlElement = CreateCommandDocument("continueFileUpload");
					XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "payload");
					xmlElement3.SetAttribute("tempFileId", num3.ToString());
					if (num2 == 0)
					{
						xmlElement3.SetAttribute("finalChunk", "1");
					}
					mD5CryptoServiceProvider = new MD5CryptoServiceProvider();
					stringBuilder.Length = 0;
					byte[] array = mD5CryptoServiceProvider.ComputeHash(array2, 0, num5);
					foreach (byte b2 in array)
					{
						stringBuilder.Append($"{b2:X2}");
					}
					xmlElement3.SetAttribute("chunkMD5", stringBuilder.ToString());
					xmlElement3.SetAttribute("chunkSize", num5.ToString());
					modInternalXMLHelperFunctions.AppendTextToElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "data"), Convert.ToBase64String(array2, 0, num5, Base64FormattingOptions.InsertLineBreaks));
					xmlDocument = ExecuteAndIfNecessaryTraceCommand("Continue file upload", xmlElement.OwnerDocument);
					if (feedback_ != null)
					{
						try
						{
							fileTransferProgressEvent.BytesSoFar = num - num2;
							feedback_.UpdateStatus(fileTransferProgressEvent);
						}
						catch (Exception)
						{
						}
					}
				}
				while (num2 != 0 && !fileTransferProgressEvent.Halted);
			}
			if (num2 > 0)
			{
				XmlElement xmlElement4 = CreateCommandDocument("cancelFileUpload");
				xmlElement4.SetAttribute("tempFileId", num3.ToString());
				ExecuteAndIfNecessaryTraceCommand("Cancelling file upload", xmlElement4.OwnerDocument);
			}
			else if (xmlDocument != null)
			{
				int attachedFileId = int.Parse(modInternalXMLHelperFunctions.GetChildElementIfThere(xmlDocument.DocumentElement, "continueFileUpload/progress").GetAttribute("fileId"));
				jtFile_.AttachedFileId = attachedFileId;
				jtFile_.ClearUpdateFlags();
			}
			if (feedback_ == null)
			{
				return;
			}
			try
			{
				if (num2 > 0)
				{
					feedback_.UpdateStatus(new FileTransferProgressEvent(num - num2, num, cancelled_: true));
				}
				else
				{
					feedback_.UpdateStatus(new FileTransferProgressEvent(num));
				}
			}
			catch (Exception)
			{
			}
		}
		catch (Exception ex3)
		{
			try
			{
				feedback_.UpdateStatus(new FileTransferProgressEvent(num - num2, num, ex3));
			}
			catch (Exception)
			{
			}
			if (!suppressExceptions_)
			{
				throw ex3;
			}
		}
	}

	private void AppendNecessaryCustomFilters(XmlElement filterElement_, List<CustomFieldFilter> customFieldFilters_)
	{
		if (customFieldFilters_ == null)
		{
			return;
		}
		foreach (CustomFieldFilter item in customFieldFilters_)
		{
			string arg = CustomFieldType.PrefixFromCustomFieldType(item.CustomFieldType);
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(filterElement_, $"{arg}CustomFieldFilter");
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, $"{arg}CustomField", item.CustomFieldId);
			switch (item.Filter.FilterType)
			{
			case CustomFieldFilterType_Enum.Text:
			{
				TextFilter textFilter = item.TextFilter;
				XmlElement parentElement_3 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "textFilter");
				AppendTextFilterContent(parentElement_3, textFilter);
				break;
			}
			case CustomFieldFilterType_Enum.Numbers:
			{
				NumberFilter numberFilter = item.NumberFilter;
				XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "numberFilter");
				if (numberFilter.Empty)
				{
					modInternalXMLHelperFunctions.AppendElement(parentNode_2, "empty");
					break;
				}
				if (numberFilter.MaxValue.HasValue || numberFilter.MinValue.HasValue)
				{
					if (numberFilter.MinValue.HasValue)
					{
						modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "minValue", numberFilter.MinValue.ToString());
					}
					if (numberFilter.MaxValue.HasValue)
					{
						modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "maxValue", numberFilter.MaxValue.ToString());
					}
					break;
				}
				throw new Exception("When using a NumberFilter, either NumberFilter.Empty must be set to True, or one of MinValue, MaxValue must be non-null.");
			}
			case CustomFieldFilterType_Enum.Dates:
			{
				DateFilter dateFilter = item.DateFilter;
				XmlElement parentElement_2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "dateFilter");
				AppendDateFilterContent(parentElement_2, dateFilter);
				break;
			}
			case CustomFieldFilterType_Enum.ListOfValues:
			{
				ListOfValuesFilter listOfValuesFilter = item.ListOfValuesFilter;
				XmlElement parentElement_ = modInternalXMLHelperFunctions.AppendElement(parentNode_, "listOfValuesFilter");
				AppendListOfValuesFilterContent(parentElement_, listOfValuesFilter);
				break;
			}
			default:
				throw new Exception($"Unsupported custom field filter type:  {item.Filter.FilterType} " + $"(custom field id={item.CustomFieldId})");
			}
		}
	}

	private void AppendTextFilterContent(XmlElement parentElement_, TextFilter textFilter_)
	{
		if (textFilter_.Empty)
		{
			modInternalXMLHelperFunctions.AppendElement(parentElement_, "empty");
			return;
		}
		XmlElement xmlElement = modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentElement_, "searchText", textFilter_.SearchText, includeEmptyTextElements_: true);
		if (textFilter_.ExactMatch)
		{
			xmlElement.SetAttribute("exactMatch", "1");
		}
	}

	private void AppendListOfValuesFilterContent(XmlElement parentElement_, ListOfValuesFilter listOfValuesFilter_)
	{
		if (listOfValuesFilter_.Invert)
		{
			parentElement_.SetAttribute("invert", "1");
		}
		XmlElement xmlElement = modInternalXMLHelperFunctions.AppendElement(parentElement_, "fieldValues");
		if (listOfValuesFilter_.Values.DoIncludeNone())
		{
			xmlElement.SetAttribute("includeNone", "1");
		}
		foreach (int value in listOfValuesFilter_.Values.Values)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "fieldValue", value);
		}
	}

	private void AppendDateFilterContent(XmlElement parentElement_, DateFilter dateFilter_)
	{
		if (dateFilter_.Empty)
		{
			modInternalXMLHelperFunctions.AppendElement(parentElement_, "empty");
			return;
		}
		if (dateFilter_.AtLeastDate.HasValue || dateFilter_.AtLeastDaysAgo.HasValue || dateFilter_.AtLeastDaysFromToday.HasValue || dateFilter_.AtMostDate.HasValue || dateFilter_.AtMostDaysAgo.HasValue || dateFilter_.AtMostDaysFromToday.HasValue)
		{
			if (dateFilter_.AtLeastDate.HasValue)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(modInternalXMLHelperFunctions.AppendElement(parentElement_, "atLeast"), "date", dateFilter_.AtLeastDate.Value.ToString("yyyy-MM-dd"));
			}
			if (dateFilter_.AtLeastDaysAgo.HasValue)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(modInternalXMLHelperFunctions.AppendElement(parentElement_, "atLeast"), "daysAgo", dateFilter_.AtLeastDaysAgo.ToString());
			}
			if (dateFilter_.AtLeastDaysFromToday.HasValue)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(modInternalXMLHelperFunctions.AppendElement(parentElement_, "atLeast"), "daysFromToday", dateFilter_.AtLeastDaysFromToday.ToString());
			}
			if (dateFilter_.AtMostDate.HasValue)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(modInternalXMLHelperFunctions.AppendElement(parentElement_, "atMost"), "date", dateFilter_.AtMostDate.Value.ToString("yyyy-MM-dd"));
			}
			if (dateFilter_.AtMostDaysAgo.HasValue)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(modInternalXMLHelperFunctions.AppendElement(parentElement_, "atMost"), "daysAgo", dateFilter_.AtMostDaysAgo.ToString());
			}
			if (dateFilter_.AtMostDaysFromToday.HasValue)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(modInternalXMLHelperFunctions.AppendElement(parentElement_, "atMost"), "daysFromToday", dateFilter_.AtMostDaysFromToday.ToString());
			}
			return;
		}
		throw new Exception("When using a DateFilter, either DateFilter.Empty must be set to True, or one of AtLeastDate, AtLeastDaysAgo, AtLeastDaysFromNow, AtMostDate, AtMostDaysAgo and AtMostDaysFromNow must be non-null.");
	}

	private void AppendAccountStatusFilterIfNecessary(XmlElement filterElement_, List<AccountStatusFilter> accountStatusFilters_)
	{
		if (accountStatusFilters_ == null)
		{
			return;
		}
		foreach (AccountStatusFilter item in accountStatusFilters_)
		{
			XmlElement xmlElement = modInternalXMLHelperFunctions.AppendElement(filterElement_, "accountStatus");
			if (item.Invert)
			{
				xmlElement.SetAttribute("invert", "1");
			}
			foreach (Account.AccountStatusType_Enum value in item.Values)
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement, "fieldValue").InnerText = Account.AccountStatusStringFromId(value);
			}
		}
	}

	private void AppendPOStatusFilterIfNecessary(XmlElement filterElement_, List<PurchaseOrderStatusFilter> purchaseOrderStatusFilters_)
	{
		if (purchaseOrderStatusFilters_ == null)
		{
			return;
		}
		foreach (PurchaseOrderStatusFilter item in purchaseOrderStatusFilters_)
		{
			XmlElement xmlElement = modInternalXMLHelperFunctions.AppendElement(filterElement_, "purchaseOrderStatus");
			if (item.Invert)
			{
				xmlElement.SetAttribute("invert", "1");
			}
			foreach (PurchaseOrder.PurchaseOrderStatusType_Enum value in item.Values)
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement, "fieldValue").InnerText = PurchaseOrder.POStatusStringFromId(value);
			}
		}
	}

	private void AppendBuiltInDateFilters<F>(XmlElement filterElement_, List<BuiltInDateFilter<F>> bidfs_)
	{
		if (bidfs_ == null)
		{
			return;
		}
		foreach (BuiltInDateFilter<F> item in bidfs_)
		{
			string text = item.Field.ToString();
			text = text.Substring(0, 1).ToLower() + text.Substring(1);
			AppendDateFilterContent(modInternalXMLHelperFunctions.AppendElement(filterElement_, text), item.Filter);
		}
	}

	private void AppendBuiltInTextFilters<F>(XmlElement filterElement_, List<BuiltInTextFilter<F>> bitfs_)
	{
		if (bitfs_ == null)
		{
			return;
		}
		foreach (BuiltInTextFilter<F> item in bitfs_)
		{
			string text = item.Field.ToString();
			text = text.Substring(0, 1).ToLower() + text.Substring(1);
			AppendTextFilterContent(modInternalXMLHelperFunctions.AppendElement(filterElement_, text), item.Filter);
		}
	}

	private void AppendBuiltInListOfValuesFilters<F>(XmlElement filterElement_, List<BuiltInListOfValuesFilter<F>> bilfs_)
	{
		if (bilfs_ == null)
		{
			return;
		}
		foreach (BuiltInListOfValuesFilter<F> item in bilfs_)
		{
			string text = item.Field.ToString();
			text = text.Substring(0, 1).ToLower() + text.Substring(1);
			AppendListOfValuesFilterContent(modInternalXMLHelperFunctions.AppendElement(filterElement_, text), item.Filter);
		}
	}

	public FormTemplate GetFormTemplate(int formTemplateId_, bool includeFields_)
	{
		List<FormTemplate> formTemplateOrTemplates = GetFormTemplateOrTemplates(includeFields_, new int[1] { formTemplateId_ });
		if (formTemplateOrTemplates.Count == 0)
		{
			return null;
		}
		return formTemplateOrTemplates[0];
	}

	public List<FormTemplate> GetFormTemplates(bool includeFields_)
	{
		return GetFormTemplateOrTemplates(includeFields_);
	}

	public List<FormTemplate> GetFormTemplates(bool includeFields_, int processId_)
	{
		return GetFormTemplateOrTemplates(includeFields_, null, new int[1] { processId_ });
	}

	public List<FormTemplate> GetFormTemplates(IEnumerable<int> formTemplateIds_, bool includeFields_)
	{
		if (formTemplateIds_ == null)
		{
			formTemplateIds_ = new int[0];
		}
		return GetFormTemplateOrTemplates(includeFields_, formTemplateIds_);
	}

	internal List<FormTemplate> GetFormTemplateOrTemplates(bool includeFields_, IEnumerable<int> formTemplateIds_ = null, IEnumerable<int> processIds_ = null)
	{
		List<FormTemplate> list = new List<FormTemplate>();
		ValidateConnected();
		bool flag = true;
		if (formTemplateIds_ != null)
		{
			flag = formTemplateIds_.GetEnumerator().MoveNext();
		}
		if (flag)
		{
			XmlElement xmlElement = CreateCommandDocument("jobFormTemplateQuery");
			XmlElement xmlElement2 = null;
			if (formTemplateIds_ != null)
			{
				xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
				foreach (int item2 in formTemplateIds_)
				{
					modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "formTemplate", item2);
				}
			}
			if (processIds_ != null)
			{
				if (xmlElement2 == null)
				{
					xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
				}
				AppendProcessesToFilter(xmlElement2, processIds_);
			}
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
			modInternalXMLHelperFunctions.AppendElements(parentNode_, new string[4] { "processes", "name", "isInactive", "seqNum" });
			if (includeFields_)
			{
				modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(parentNode_, "formTemplateField"), new string[4] { "name", "isCustomSort", "dataType", "isInactive" });
			}
			foreach (XmlElement item3 in ExecuteAndIfNecessaryTraceCommand("Job Form Template query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("jobFormTemplateQuery/formTemplate"))
			{
				string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "name");
				int id_ = int.Parse(item3.GetAttribute("id"));
				bool isInactive_ = "1" == item3.GetAttribute("isInactive");
				List<int> processes_ = BuildProcessIdList(modInternalXMLHelperFunctions.GetChildElementIfThere(item3, "processes"));
				FormTemplate formTemplate = new FormTemplate(id_, textOfChildIfThere, isInactive_, processes_);
				if (includeFields_)
				{
					formTemplate.FormFields = new List<FormTemplateField>();
					foreach (XmlElement item4 in item3.SelectNodes("formTemplateFields/formTemplateField"))
					{
						int id_2 = int.Parse(item4.GetAttribute("id"));
						string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item4, "name");
						string attribute = item4.GetAttribute("dataType");
						bool isCustomSort_ = "1" == item4.GetAttribute("isCustomSort");
						bool isInactive_2 = "1" == item4.GetAttribute("isInactive");
						FormTemplateField item = new FormTemplateField(id_2, textOfChildIfThere2, isCustomSort_, attribute, isInactive_2);
						formTemplate.FormFields.Add(item);
					}
				}
				list.Add(formTemplate);
			}
		}
		return list;
	}

	public void ReorderFormTemplateLOVFieldValues(int formTemplateFieldId_, IEnumerable<int> fieldValueIds_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("formTemplateLOVFieldValueReorder");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "formTemplateFieldType");
		xmlElement2.SetAttribute("id", formTemplateFieldId_.ToString());
		foreach (int item in fieldValueIds_)
		{
			modInternalXMLHelperFunctions.AppendElement(xmlElement2, "formTemplateFieldValue").SetAttribute("id", item.ToString());
		}
		if (xmlElement.SelectSingleNode("*") != null)
		{
			ExecuteAndIfNecessaryTraceCommand("Form Template List of Values field reorder", xmlElement.OwnerDocument);
		}
	}

	public List<FormTemplateLOVFieldValue> GetFormTemplateLOVFieldValues(int formTemplateFieldId_)
	{
		ValidateConnected();
		List<FormTemplateLOVFieldValue> list = new List<FormTemplateLOVFieldValue>();
		XmlElement xmlElement = CreateCommandDocument("formTemplateLOVFieldValueQuery");
		modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "formTemplateFieldType", formTemplateFieldId_);
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[4] { "value", "isInactive", "seqNum", "displayColor" });
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Form Template LOV field query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("formTemplateLOVFieldValueQuery/formTemplateFieldType/formTemplateFieldValue"))
		{
			int id_ = int.Parse(item.GetAttribute("id"));
			bool isInactive_ = "1" == item.GetAttribute("isInactive");
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "value");
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "displayColor");
			int? seqNum_ = null;
			if (item.HasAttribute("seqNum"))
			{
				seqNum_ = int.Parse(item.GetAttribute("seqNum"));
			}
			list.Add(new FormTemplateLOVFieldValue(id_, textOfChildIfThere, isInactive_, textOfChildIfThere2, seqNum_));
		}
		return list;
	}

	public InventoryCount GetInventoryCount(int inventoryCountId_)
	{
		List<InventoryCount> inventoryCounts = GetInventoryCounts(new int[1] { inventoryCountId_ }, all_: false);
		if (inventoryCounts.Count > 0)
		{
			return inventoryCounts[0];
		}
		return null;
	}

	public List<InventoryCount> GetInventoryCounts()
	{
		return GetInventoryCounts(null, all_: true);
	}

	public List<InventoryCount> GetInventoryCounts(IEnumerable<int> inventoryCountIds_)
	{
		return GetInventoryCounts(inventoryCountIds_, all_: false);
	}

	private List<InventoryCount> GetInventoryCounts(IEnumerable<int> inventoryCountIds_, bool all_)
	{
		List<InventoryCount> list = new List<InventoryCount>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("inventoryCountQuery");
		if (!all_)
		{
			flag = true;
			if (inventoryCountIds_ != null)
			{
				XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
				foreach (int item in inventoryCountIds_)
				{
					flag = false;
					modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "inventoryCount", item);
				}
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("InventoryCount query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("inventoryCountQuery/inventoryCount"))
			{
				list.Add(GetInventoryCountFromInventoryCountElement(item2));
			}
		}
		return list;
	}

	private InventoryCount GetInventoryCountFromInventoryCountElement(XmlElement inventoryCountElement_)
	{
		InventoryCount inventoryCount = new InventoryCount(int.Parse(inventoryCountElement_.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryCountElement_, "name"), ParseDateTime(modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryCountElement_, "frozenTimestamp")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryCountElement_, "frozenBy"));
		inventoryCount.ClearUpdateFlags();
		return inventoryCount;
	}

	public void DeleteInventoryCount(int inventoryCountId_)
	{
		DeleteInventoryCounts(new int[1] { inventoryCountId_ });
	}

	public void DeleteInventoryCounts(IEnumerable<int> inventoryCountIds_)
	{
		DeleteByIds(inventoryCountIds_, "inventoryCount", "Inventory Count");
	}

	public int CreateInventoryCount(InventoryCount inventoryCount_)
	{
		if (inventoryCount_.InventoryCountId != 0)
		{
			throw new Exception("When creating an inventory count, you must use a new InventoryCount object");
		}
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("inventoryCountCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "inventoryCount");
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", inventoryCount_.InventoryCountName, includeEmptyTextElements_: true);
		if (inventoryCount_.ModifiedFrozen && inventoryCount_.Frozen)
		{
			xmlElement2.SetAttribute("frozen", "1");
		}
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("InventoryCount create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("inventoryCountCreate/inventoryCount");
		inventoryCount_.SetInventoryCountId(int.Parse(xmlElement3.GetAttribute("id")));
		inventoryCount_.ClearUpdateFlags();
		return inventoryCount_.InventoryCountId;
	}

	public void UpdateInventoryCount(InventoryCount inventoryCount_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("inventoryCountUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "inventoryCount");
		xmlElement2.SetAttribute("id", $"{inventoryCount_.InventoryCountId}");
		if (inventoryCount_.ModifiedFrozen)
		{
			xmlElement2.SetAttribute("frozen", $"{(inventoryCount_.Frozen ? 1 : 0)}");
		}
		if (inventoryCount_.ModifiedName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", inventoryCount_.InventoryCountName, includeEmptyTextElements_: true);
		}
		ExecuteAndIfNecessaryTraceCommand("InventoryCount update", xmlElement.OwnerDocument);
		inventoryCount_.ClearUpdateFlags();
	}

	public Guid CreateInventoryCountDetail(InventoryCountDetail inventoryCountDetail_)
	{
		if (inventoryCountDetail_.InventoryCountId == 0)
		{
			throw new Exception("When creating an inventory count detail, you must use a new InventoryCountDetail object");
		}
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("inventoryCountDetailCreate");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "inventoryCountDetail");
		modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "inventoryCount", inventoryCountDetail_.InventoryCountId.ToString());
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentNode_, "countType", inventoryCountDetail_.CountType);
		if (!inventoryCountDetail_.IdTypeOnCreate.HasValue)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(modInternalXMLHelperFunctions.AppendElement(parentNode_, "serialNumber"), "name", inventoryCountDetail_.SerialNumberName, includeEmptyTextElements_: true);
		}
		else if (inventoryCountDetail_.IdTypeOnCreate.Value == InventoryCountDetail.IdType_Enum.PurchaseProductVariant_IdType)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseProductVariant", inventoryCountDetail_.PurchaseProductVariantId);
		}
		else
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "serialNumber", $"{inventoryCountDetail_.SerialNumberId}");
		}
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentNode_, "quantity", inventoryCountDetail_.Quantity);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentNode_, "location", inventoryCountDetail_.Location);
		XmlElement xmlElement2 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("InventoryCountDetail create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("inventoryCountDetailCreate/inventoryCountDetail");
		inventoryCountDetail_.Id = new Guid(xmlElement2.GetAttribute("id"));
		inventoryCountDetail_.ClearUpdateFlags();
		return inventoryCountDetail_.Id;
	}

	public List<InventoryCountDetail> GetInventoryCountDetails(int inventoryCountId_)
	{
		ValidateConnected();
		List<InventoryCountDetail> list = new List<InventoryCountDetail>();
		XmlElement xmlElement = CreateCommandDocument("inventoryCountDetailQuery");
		modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "inventoryCount", inventoryCountId_);
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("InventoryCountDetail query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("inventoryCountDetailQuery/inventoryCountDetail"))
		{
			list.Add(GetInventoryCountDetailFromInventoryCountDetailElement(item));
		}
		return list;
	}

	public InventoryCountDetail GetInventoryCountDetail(Guid inventoryCountDetailId_)
	{
		List<InventoryCountDetail> inventoryCountDetails = GetInventoryCountDetails(new Guid[1] { inventoryCountDetailId_ });
		if (inventoryCountDetails.Count > 0)
		{
			return inventoryCountDetails[0];
		}
		return null;
	}

	public List<InventoryCountDetail> GetInventoryCountDetails(IEnumerable<Guid> inventoryCountDetailIds_)
	{
		List<InventoryCountDetail> list = new List<InventoryCountDetail>();
		if (inventoryCountDetailIds_ != null)
		{
			XmlElement xmlElement = CreateCommandDocument("inventoryCountDetailQuery");
			bool flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (Guid item in inventoryCountDetailIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElement(parentNode_, "inventoryCountDetail").SetAttribute("id", item.ToString("D").ToUpper());
			}
			if (!flag)
			{
				ValidateConnected();
				modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
				foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("InventoryCountDetail query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("inventoryCountDetailQuery/inventoryCountDetail"))
				{
					list.Add(GetInventoryCountDetailFromInventoryCountDetailElement(item2));
				}
			}
		}
		return list;
	}

	private InventoryCountDetail GetInventoryCountDetailFromInventoryCountDetailElement(XmlElement element_)
	{
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, "purchaseProduct");
		XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, "serialNumber");
		InventoryCountDetail inventoryCountDetail = new InventoryCountDetail();
		inventoryCountDetail.CountedBy = modInternalXMLHelperFunctions.GetTextOfChildIfThere(element_, "countedBy");
		inventoryCountDetail.CountTimestamp = ParseDateTime(modInternalXMLHelperFunctions.GetTextOfChildIfThere(element_, "countTimestamp")).Value;
		inventoryCountDetail.CountType = modInternalXMLHelperFunctions.GetTextOfChildIfThere(element_, "countType");
		inventoryCountDetail.Location = modInternalXMLHelperFunctions.GetTextOfChildIfThere(element_, "location");
		XmlElement childElementIfThere3 = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, "purchaseProductVariant");
		inventoryCountDetail.PurchaseProductVariantId = int.Parse(childElementIfThere3.GetAttribute("id"));
		inventoryCountDetail.PurchaseProductVariantName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere3, "name");
		inventoryCountDetail.PurchaseProductId = int.Parse(childElementIfThere.GetAttribute("id"));
		inventoryCountDetail.PurchaseProductName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name");
		inventoryCountDetail.Quantity = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(element_, "quantity"));
		inventoryCountDetail.SerialNumberId = GetNullableIntFromAttribute(childElementIfThere2, "id");
		inventoryCountDetail.SerialNumberName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere2, "name");
		inventoryCountDetail.Id = new Guid(element_.GetAttribute("id"));
		inventoryCountDetail.ClearUpdateFlags();
		return inventoryCountDetail;
	}

	public void DeleteInventoryCountDetail(Guid inventoryCountDetailId_)
	{
		DeleteInventoryCountDetails(new Guid[1] { inventoryCountDetailId_ });
	}

	public void DeleteInventoryCountDetails(IEnumerable<Guid> inventoryCountDetailIds_)
	{
		List<string> list = new List<string>();
		foreach (Guid item in inventoryCountDetailIds_)
		{
			list.Add(item.ToString("D").ToUpper());
		}
		DeleteByIds(list, "inventoryCountDetail", "Inventory Count Detail");
	}

	public List<InventoryLocation> GetInventoryLocations()
	{
		return GetInventoryLocationOrInventoryLocations(null);
	}

	private List<InventoryLocation> GetInventoryLocationOrInventoryLocations(int? inventoryLocationId_)
	{
		List<InventoryLocation> list = new List<InventoryLocation>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("inventoryLocationQuery");
		if (inventoryLocationId_.HasValue)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "inventoryLocation", inventoryLocationId_.Value);
		}
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[2] { "name", "isInactive" });
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("InventoryLocation query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("inventoryLocationQuery/inventoryLocation"))
		{
			list.Add(GetInventoryLocationFromInventoryLocationElement(item));
		}
		return list;
	}

	public InventoryLocation GetInventoryLocation(int inventoryLocationId_)
	{
		InventoryLocation inventoryLocation = null;
		List<InventoryLocation> inventoryLocationOrInventoryLocations = GetInventoryLocationOrInventoryLocations(inventoryLocationId_);
		if (inventoryLocationOrInventoryLocations.Count == 0)
		{
			return null;
		}
		return inventoryLocationOrInventoryLocations[0];
	}

	public void DeleteInventoryLocation(int inventoryLocationId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("inventoryLocationDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "inventoryLocation", inventoryLocationId_);
		ExecuteAndIfNecessaryTraceCommand("InventoryLocation delete", xmlElement.OwnerDocument);
	}

	private InventoryLocation GetInventoryLocationFromInventoryLocationElement(XmlElement inventoryLocationElement_)
	{
		InventoryLocation inventoryLocation = null;
		if (inventoryLocationElement_ == null)
		{
			return null;
		}
		bool isInactive = "1" == inventoryLocationElement_.GetAttribute("isInactive");
		return new InventoryLocation(int.Parse(inventoryLocationElement_.GetAttribute("id")))
		{
			InventoryLocationName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryLocationElement_, "name"),
			IsInactive = isInactive
		};
	}

	public int CreateInventoryLocation(InventoryLocation inventoryLocation_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("inventoryLocationCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "inventoryLocation");
		if (inventoryLocation_.IsInactive)
		{
			xmlElement2.SetAttribute("isInactive", "1");
		}
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", inventoryLocation_.InventoryLocationName, includeEmptyTextElements_: true);
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("InventoryLocation create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("inventoryLocationCreate/inventoryLocation");
		inventoryLocation_.InventoryLocationId = int.Parse(xmlElement3.GetAttribute("id"));
		inventoryLocation_.ClearUpdateFlags();
		return inventoryLocation_.InventoryLocationId;
	}

	public void UpdateInventoryLocation(InventoryLocation inventoryLocation_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("inventoryLocationUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "inventoryLocation");
		xmlElement2.SetAttribute("id", $"{inventoryLocation_.InventoryLocationId}");
		if (inventoryLocation_.ModifiedIsInactive)
		{
			xmlElement2.SetAttribute("isInactive", $"{(inventoryLocation_.IsInactive ? 1 : 0)}");
		}
		if (inventoryLocation_.ModifiedInventoryLocationName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", inventoryLocation_.InventoryLocationName, includeEmptyTextElements_: true);
		}
		ExecuteAndIfNecessaryTraceCommand("InventoryLocation update", xmlElement.OwnerDocument);
		inventoryLocation_.ClearUpdateFlags();
	}

	public List<Job> GetJobsForAccount(int accountId_, bool includeContacts_ = false, bool includeJobPhases_ = false)
	{
		return GetJobsForAccount(accountId_, includeContacts_, includeJobPhases_, null);
	}

	public List<Job> GetJobsForAccount(int accountId_, int processId_, bool includeContacts_ = false, bool includeJobPhases_ = false)
	{
		return GetJobsForAccount(accountId_, includeContacts_, includeJobPhases_, new int[1] { processId_ });
	}

	private List<Job> GetJobsForAccount(int accountId_, bool includeContacts_, bool includeJobPhases_, IEnumerable<int> processIds_)
	{
		List<Job> list = new List<Job>();
		foreach (XmlElement item in ExecuteGetJobQuery(includeContacts_, includeJobPhases_, accountId_, null, processIds_).DocumentElement.SelectNodes("jobQuery/job"))
		{
			list.Add(GetJobFromJobElement(item));
		}
		return list;
	}

	public Job GetJob(int jobId_, bool includeContacts_ = false, bool includeJobPhases_ = false)
	{
		XmlElement documentElement = ExecuteGetJobQuery(includeContacts_, includeJobPhases_, null, new int[1] { jobId_ }).DocumentElement;
		return GetJobFromJobElement(modInternalXMLHelperFunctions.GetChildElementIfThere(documentElement, "jobQuery/job"));
	}

	public List<Job> GetJobs(IEnumerable<int> jobIds_, bool includeContacts_ = false, bool includeJobPhases_ = false)
	{
		XmlElement documentElement = ExecuteGetJobQuery(includeContacts_, includeJobPhases_, null, jobIds_).DocumentElement;
		List<Job> list = new List<Job>();
		foreach (XmlElement item in documentElement.SelectNodes("jobQuery/job"))
		{
			list.Add(GetJobFromJobElement(item));
		}
		return list;
	}

	public List<Job> GetJobs(JobFilter jobFilter_, PagingOptions pagingOptions_, bool includeContacts_ = false, bool includeJobPhases_ = false)
	{
		if (jobFilter_ == null)
		{
			throw new APIException("Missing 'JobFilter' parameter in call to GetJobs()", APIException.APIErrorCodes_Enum.GeneralException);
		}
		XmlElement documentElement = ExecuteGetJobQuery(includeContacts_, includeJobPhases_, null, null, null, jobFilter_, pagingOptions_).DocumentElement;
		List<Job> list = new List<Job>();
		if ((pagingOptions_?.TotalRecords).HasValue)
		{
			pagingOptions_.TotalRecords = Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(documentElement, "jobQuery").GetAttribute("totalRecords"));
		}
		foreach (XmlElement item in documentElement.SelectNodes("jobQuery/job"))
		{
			list.Add(GetJobFromJobElement(item));
		}
		return list;
	}

	public List<Job> GetJobsOfPurchaseOrders(IEnumerable<int> purchaseOrderIds_, IEnumerable<int> processIds_ = null, bool includeContacts_ = false, bool includeJobPhases_ = false)
	{
		XmlElement documentElement = ExecuteGetJobQuery(includeContacts_, includeJobPhases_, null, null, processIds_, null, null, purchaseOrderIds_).DocumentElement;
		List<Job> list = new List<Job>();
		foreach (XmlElement item in documentElement.SelectNodes("jobQuery/job"))
		{
			list.Add(GetJobFromJobElement(item));
		}
		return list;
	}

	public void AddPurchaseOrdersToJob(IEnumerable<int> purchaseOrderIds_, int jobId_)
	{
		CreateJobPOs(new int[1] { jobId_ }, purchaseOrderIds_);
	}

	public void AddPurchaseOrderToJob(int purchaseOrderId_, int jobId_)
	{
		CreateJobPOs(new int[1] { jobId_ }, new int[1] { purchaseOrderId_ });
	}

	private void CreateJobPOs(IEnumerable<int> jobIds_, IEnumerable<int> poIds_)
	{
		if (jobIds_ == null || poIds_ == null || !jobIds_.GetEnumerator().MoveNext() || !poIds_.GetEnumerator().MoveNext())
		{
			return;
		}
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobPurchaseOrderCreate");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "jobs");
		XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "purchaseOrders");
		foreach (int item in jobIds_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "job", item);
		}
		foreach (int item2 in poIds_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_2, "purchaseOrder", item2);
		}
		ExecuteAndIfNecessaryTraceCommand("Job/PO Creation", xmlElement.OwnerDocument);
	}

	public void RemovePurchaseOrderFromJob(int purchaseOrderId_, int jobId_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobPurchaseOrderDelete");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "jobPurchaseOrder");
		xmlElement2.SetAttribute("jobId", $"{jobId_}");
		xmlElement2.SetAttribute("purchaseOrderId", $"{purchaseOrderId_}");
		ExecuteAndIfNecessaryTraceCommand("Job/PO Deletion", xmlElement.OwnerDocument);
	}

	public void UpdatePurchaseProductVariantAllocation(PurchaseProductVariantAllocation purchaseProductVariantAllocation_)
	{
		UpdatePurchaseProductVariantAllocations(new PurchaseProductVariantAllocation[1] { purchaseProductVariantAllocation_ });
	}

	public void UpdatePurchaseProductVariantAllocations(IEnumerable<PurchaseProductVariantAllocation> purchaseProductVariantAllocations_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("purchaseProductVariantAllocationUpdate");
		bool flag = true;
		foreach (PurchaseProductVariantAllocation item in purchaseProductVariantAllocations_)
		{
			flag = false;
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "purchaseProductVariantAllocation");
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "jobActivity", item.JobActivityId);
			int productId_ = 0;
			ProductAttributeValueContainer attrs_ = null;
			bool usePPVId_ = false;
			int ppvId_ = item.PurchaseProductVariantId;
			if (item.PurchaseProductVariantForCreate == null)
			{
				usePPVId_ = true;
			}
			else
			{
				productId_ = item.PurchaseProductVariantForCreate.ProductId;
				attrs_ = item.PurchaseProductVariantForCreate.ProductAttributeValues;
				if (item.PurchaseProductVariantForCreate.ProductVariantId != 0 || item.PurchaseProductVariantForCreate.ProductId == 0)
				{
					usePPVId_ = true;
					ppvId_ = item.PurchaseProductVariantForCreate.ProductVariantId;
				}
			}
			AppendPPVCommandElements(xmlElement2, ppvId_, productId_, attrs_, usePPVId_);
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "quantity", item.Quantity.ToString("###0.#####"), includeEmptyTextElements_: true);
		}
		if (!flag)
		{
			ExecuteAndIfNecessaryTraceCommand("PurchaseProductVariantAllocation update", xmlElement.OwnerDocument);
		}
	}

	public void UpdateSerialNumberAllocation(SerialNumberAllocation serialNumberAllocation_)
	{
		UpdateSerialNumberAllocations(new SerialNumberAllocation[1] { serialNumberAllocation_ });
	}

	public void UpdateSerialNumberAllocations(IEnumerable<SerialNumberAllocation> serialNumberAllocations_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("serialNumberAllocationUpdate");
		bool flag = true;
		foreach (SerialNumberAllocation item in serialNumberAllocations_)
		{
			flag = false;
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "serialNumberAllocation");
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "jobActivity", item.JobActivityId);
			AppendSerialNumberSpecification(xmlElement2, item);
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "quantity", item.Quantity.ToString("###0.#####"), includeEmptyTextElements_: true);
		}
		if (!flag)
		{
			ExecuteAndIfNecessaryTraceCommand("SerialNumberAllocation update", xmlElement.OwnerDocument);
		}
	}

	private XmlElement AppendSerialNumberSpecification(XmlElement parentElement_, SerialNumberAllocation serialNumberAllocation_)
	{
		XmlElement xmlElement = modInternalXMLHelperFunctions.AppendElement(parentElement_, "serialNumber");
		if (serialNumberAllocation_.NullableSerialNumberId.HasValue)
		{
			xmlElement.SetAttribute("id", $"{serialNumberAllocation_.SerialNumberId}");
		}
		else
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "name", serialNumberAllocation_.SerialNumberName, includeEmptyTextElements_: true);
		}
		return xmlElement;
	}

	public void DeleteSerialNumberAllocation(SerialNumberAllocation serialNumberAllocation_)
	{
		DeleteSerialNumberAllocations(new SerialNumberAllocation[1] { serialNumberAllocation_ });
	}

	public void DeleteSerialNumberAllocations(IEnumerable<SerialNumberAllocation> serialNumberAllocations_)
	{
		XmlElement xmlElement = CreateCommandDocument("serialNumberAllocationDelete");
		bool flag = true;
		foreach (SerialNumberAllocation item in serialNumberAllocations_)
		{
			flag = false;
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "serialNumberAllocation");
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "jobActivity", item.JobActivityId);
			AppendSerialNumberSpecification(xmlElement2, item);
		}
		if (!flag)
		{
			ValidateConnected();
			ExecuteAndIfNecessaryTraceCommand("SerialNumberAllocation Delete", xmlElement.OwnerDocument);
		}
	}

	public void DeleteJobActivityMaterial(JobActivityMaterial jobActivityMaterial_)
	{
		DeleteJobActivityMaterial(new JobActivityMaterial[1] { jobActivityMaterial_ });
	}

	public void DeleteJobActivityMaterial(IEnumerable<JobActivityMaterial> jobActivityMaterial_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobActivityMaterialDelete");
		foreach (JobActivityMaterial item in jobActivityMaterial_)
		{
			if (item.PurchaseProductVariantId == 0)
			{
				throw new Exception("No PurchaseProductVariantId has been set!\n\nWhen deleting JobActivityMaterial, you must use refer to the JobActivityMaterial using the JobActivityId and PurchaseProductVariantId");
			}
			if (item.JobActivityId == 0)
			{
				throw new Exception("No JobActivityId has been set!\n\nWhen deleting JobActivityMaterial, you must use refer to the JobActivityMaterial using the JobActivityId and PurchaseProductVariantId");
			}
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "jobActivityMaterial");
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "jobActivity", item.JobActivityId);
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseProductVariant", item.PurchaseProductVariantId);
		}
		ExecuteAndIfNecessaryTraceCommand("Delete JobActivityMaterial", xmlElement.OwnerDocument);
	}

	public void UpdateJobActivityMaterial(JobActivityMaterial jobActivityMaterial_)
	{
		UpdateJobActivityMaterial(new JobActivityMaterial[1] { jobActivityMaterial_ });
	}

	public void UpdateJobActivityMaterial(IEnumerable<JobActivityMaterial> jobActivityMaterial_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobActivityMaterialUpdate");
		bool flag = true;
		foreach (JobActivityMaterial item in jobActivityMaterial_)
		{
			flag = false;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "jobActivityMaterial");
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "jobActivity", item.JobActivityId);
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "purchaseProductVariantAllocation");
			int productId_ = 0;
			ProductAttributeValueContainer attrs_ = null;
			bool usePPVId_ = false;
			int ppvId_ = item.PurchaseProductVariantId;
			if (item.PurchaseProductVariantForCreate == null)
			{
				usePPVId_ = true;
			}
			else
			{
				productId_ = item.PurchaseProductVariantForCreate.ProductId;
				attrs_ = item.PurchaseProductVariantForCreate.ProductAttributeValues;
				if (item.PurchaseProductVariantForCreate.ProductVariantId != 0 || item.PurchaseProductVariantForCreate.ProductId == 0)
				{
					usePPVId_ = true;
					ppvId_ = item.PurchaseProductVariantForCreate.ProductVariantId;
				}
			}
			AppendPPVCommandElements(xmlElement2, ppvId_, productId_, attrs_, usePPVId_);
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "quantity", item.PurchaseProductVariantAllocation.Quantity.ToString("###0.#####"), includeEmptyTextElements_: true);
			foreach (SerialNumberAllocation serialNumberAllocation in item.SerialNumberAllocations)
			{
				XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "serialNumberAllocation");
				AppendSerialNumberSpecification(xmlElement3, serialNumberAllocation);
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement3, "quantity", serialNumberAllocation.Quantity.ToString("###0.#####"), includeEmptyTextElements_: true);
			}
		}
		if (!flag)
		{
			ExecuteAndIfNecessaryTraceCommand("JobActivityMaterial update", xmlElement.OwnerDocument);
		}
	}

	public List<JobActivityMaterial> GetJobActivityMaterialForJob(int jobId_)
	{
		return GetJobActivityMaterial(new int[1] { jobId_ }, null);
	}

	public List<JobActivityMaterial> GetJobActivityMaterialForJobs(IEnumerable<int> jobIds_)
	{
		return GetJobActivityMaterial(jobIds_, null);
	}

	public List<JobActivityMaterial> GetJobActivityMaterialForJobActivity(int jobActivityId_)
	{
		return GetJobActivityMaterial(null, new int[1] { jobActivityId_ });
	}

	public List<JobActivityMaterial> GetJobActivityMaterialForJobActivities(IEnumerable<int> jobActivityIds_)
	{
		return GetJobActivityMaterial(null, jobActivityIds_);
	}

	private List<JobActivityMaterial> GetJobActivityMaterial(IEnumerable<int> jobIds_, IEnumerable<int> jobActivityIds_)
	{
		List<JobActivityMaterial> list = new List<JobActivityMaterial>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("jobActivityMaterialQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (jobIds_ != null)
		{
			foreach (int item in jobIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "job", item);
			}
		}
		if (jobActivityIds_ != null)
		{
			foreach (int item2 in jobActivityIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "jobActivity", item2);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item3 in ExecuteAndIfNecessaryTraceCommand("JobActivityMaterial query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("jobActivityMaterialQuery/jobActivityMaterial"))
			{
				list.Add(GetJobActivityMaterialFromJobActivityMaterialElement(item3));
			}
		}
		return list;
	}

	private JobActivityMaterial GetJobActivityMaterialFromJobActivityMaterialElement(XmlElement element_)
	{
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, "purchaseProductVariantAllocation");
		XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(childElementIfThere, "purchaseProductVariant");
		XmlElement childElementIfThere3 = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, "jobActivity");
		XmlElement childElementIfThere4 = modInternalXMLHelperFunctions.GetChildElementIfThere(childElementIfThere3, "jobActivityType");
		XmlElement childElementIfThere5 = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, "job");
		int pvId_ = int.Parse(childElementIfThere2.GetAttribute("id"));
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere2, "name");
		int jaId_ = int.Parse(childElementIfThere3.GetAttribute("id"));
		int atId_ = int.Parse(childElementIfThere4.GetAttribute("id"));
		string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere4, "name");
		decimal unserializedQuantity_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "quantity"));
		int jobId_ = int.Parse(childElementIfThere5.GetAttribute("id"));
		string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere5, "name");
		JobActivityMaterial jobActivityMaterial = new JobActivityMaterial(null, pvId_, textOfChildIfThere, jobId_, textOfChildIfThere3, jaId_, atId_, textOfChildIfThere2, unserializedQuantity_);
		foreach (XmlElement item in element_.SelectNodes("serialNumberAllocation"))
		{
			int value = Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(item, "serialNumber").GetAttribute("id"));
			string textOfChildIfThere4 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "serialNumber/name");
			string textOfChildIfThere5 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "quantity");
			jobActivityMaterial.SerialNumberAllocations.AddAllocation(new SerialNumberAllocation(value, textOfChildIfThere4, pvId_, textOfChildIfThere, jobId_, textOfChildIfThere3, jaId_, atId_, textOfChildIfThere2, Convert.ToDecimal(textOfChildIfThere5)));
		}
		return jobActivityMaterial;
	}

	private Job GetJobFromJobElement(XmlElement jobElement_)
	{
		Job job = null;
		if (jobElement_ != null)
		{
			DateTime value = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(jobElement_, "creationDate")).Value;
			Salesperson salespersonFromSalespersonElement = GetSalespersonFromSalespersonElement(modInternalXMLHelperFunctions.GetChildElementIfThere(jobElement_, "salesperson"));
			Address addressFromAddressElement = GetAddressFromAddressElement(modInternalXMLHelperFunctions.GetChildElementIfThere(jobElement_, "address"));
			XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(jobElement_, "account");
			int jobId_ = int.Parse(jobElement_.GetAttribute("id"));
			List<JobPhase> list = new List<JobPhase>();
			XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(jobElement_, "jobPhases");
			if (childElementIfThere2 != null)
			{
				foreach (XmlElement item in childElementIfThere2.SelectNodes("jobPhase"))
				{
					list.Add(GetJobPhaseFromJobPhaseElement(item, jobId_));
				}
			}
			XmlElement childElementIfThere3 = modInternalXMLHelperFunctions.GetChildElementIfThere(jobElement_, "process");
			job = new Job(jobId_)
			{
				JobName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(jobElement_, "name"),
				ProcessId = int.Parse(childElementIfThere3.GetAttribute("id")),
				IsComplete = ("complete" == jobElement_.GetAttribute("jobStatus")),
				JobPhases = list,
				Notes = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(jobElement_, "notes")),
				CreationDate = value,
				Address = addressFromAddressElement,
				AccountId = int.Parse(childElementIfThere.GetAttribute("id")),
				AccountName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name"),
				CustomFieldValues = GetCustomFieldValuesForObject(jobElement_)
			};
			XmlNode childElementIfThere4 = modInternalXMLHelperFunctions.GetChildElementIfThere(jobElement_, "jobContacts");
			if (childElementIfThere4 != null)
			{
				job.Contacts.Clear();
				foreach (XmlElement item2 in childElementIfThere4.SelectNodes("jobContact"))
				{
					Address addressFromAddressElement2 = GetAddressFromAddressElement(item2);
					job.Contacts.AddJobContact(new JobContact(int.Parse(item2.GetAttribute("id")), addressFromAddressElement2));
				}
			}
			if (salespersonFromSalespersonElement != null)
			{
				job.SetSalesperson(salespersonFromSalespersonElement.SalespersonId, salespersonFromSalespersonElement.SalespersonName);
			}
			job.SetProcessName(modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere3, "name"));
			job.ClearUpdateFlags();
		}
		return job;
	}

	public List<SerialNumberAllocation> GetSerialNumberAllocations(IEnumerable<int> serialNumberIds_)
	{
		List<SerialNumberAllocation> list = new List<SerialNumberAllocation>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("serialNumberAllocationQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (serialNumberIds_ != null)
		{
			foreach (int item in serialNumberIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "serialNumber", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("JobActivityMaterial query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("serialNumberAllocationQuery/serialNumberAllocation"))
			{
				XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(item2, "serialNumber");
				string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name");
				XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(item2, "purchaseProductVariant");
				string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere2, "name");
				XmlElement childElementIfThere3 = modInternalXMLHelperFunctions.GetChildElementIfThere(item2, "job");
				string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere3, "name");
				XmlElement childElementIfThere4 = modInternalXMLHelperFunctions.GetChildElementIfThere(item2, "jobActivity");
				XmlElement childElementIfThere5 = modInternalXMLHelperFunctions.GetChildElementIfThere(childElementIfThere4, "jobActivityType");
				string textOfChildIfThere4 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere5, "name");
				decimal quantity_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "quantity"));
				list.Add(new SerialNumberAllocation(Convert.ToInt32(childElementIfThere.GetAttribute("id")), textOfChildIfThere, Convert.ToInt32(childElementIfThere2.GetAttribute("id")), textOfChildIfThere2, Convert.ToInt32(childElementIfThere3.GetAttribute("id")), textOfChildIfThere3, Convert.ToInt32(childElementIfThere4.GetAttribute("id")), Convert.ToInt32(childElementIfThere5.GetAttribute("id")), textOfChildIfThere4, quantity_));
			}
		}
		return list;
	}

	private XmlDocument ExecuteGetJobQuery(bool includeContacts_, bool includeJobPhases_, int? accountId_ = null, IEnumerable<int> jobIds_ = null, IEnumerable<int> processIds_ = null, JobFilter jobFilter_ = null, PagingOptions pagingOptions_ = null, IEnumerable<int> relatedPOIds_ = null)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobQuery");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (jobFilter_ != null)
		{
			if (jobFilter_.ProcessId < 1)
			{
				throw new APIException($"Invalid Process Id={jobFilter_.ProcessId}", APIException.APIErrorCodes_Enum.GeneralException);
			}
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "process", jobFilter_.ProcessId);
		}
		if (relatedPOIds_ != null)
		{
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement2, "purchaseOrders");
			foreach (int item in relatedPOIds_)
			{
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseOrder", item);
			}
		}
		if (processIds_ != null)
		{
			if (!processIds_.GetEnumerator().MoveNext())
			{
				throw new APIException("Invalid Job Query. Empty set of Process Ids listed.", APIException.APIErrorCodes_Enum.InvalidRequestDocument);
			}
			XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(xmlElement2, "processes");
			foreach (int item2 in processIds_)
			{
				ValidatePositiveId(item2, "Process", "Job");
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_2, "process", item2);
			}
		}
		if (accountId_.HasValue)
		{
			ValidatePositiveId(accountId_.Value, "Account", "Account");
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "account", accountId_.Value);
		}
		else if (jobIds_ != null)
		{
			foreach (int item3 in jobIds_)
			{
				ValidatePositiveId(item3, "Job", "Job");
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "job", item3);
			}
		}
		AppendViewFilterIfNecessary(xmlElement2, jobFilter_?.ViewId);
		AppendNecessaryCustomFilters(xmlElement2, jobFilter_?.CustomFieldFilters);
		AppendBuiltInTextFilters(xmlElement2, jobFilter_?.TextFilters);
		AppendBuiltInListOfValuesFilters(xmlElement2, jobFilter_?.ListOfValuesFilters);
		if ((jobFilter_?.JobStatus).HasValue)
		{
			if (jobFilter_.JobStatus.Value == Job.JobStatus_Enum.jsActive)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "jobStatus", "active");
			}
			else
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "jobStatus", "complete");
			}
		}
		if (pagingOptions_ == null)
		{
			if (jobFilter_ != null)
			{
				throw new APIException("Paging options are required when issuing a filtered Jobs query.", APIException.APIErrorCodes_Enum.GeneralException);
			}
		}
		else
		{
			AppendPagingSpec(xmlElement, pagingOptions_.FirstRecord, pagingOptions_.PageSize);
		}
		XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		if (includeContacts_)
		{
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "jobContact"), AddressIncludeFields());
		}
		if (includeJobPhases_)
		{
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "jobPhase"), "all");
		}
		if (pagingOptions_ != null)
		{
			modInternalXMLHelperFunctions.AppendElement(xmlElement3, "totalRecords");
		}
		modInternalXMLHelperFunctions.AppendElement(xmlElement3, "jobStatus");
		AddObjectCustomFieldIncludeElements(xmlElement3, "job");
		modInternalXMLHelperFunctions.AppendElements(xmlElement3, new string[3] { "name", "creationDate", "notes" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "process"), "name");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "salesperson"), "name");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "account"), "name");
		AppendAddressInclude(xmlElement3);
		return ExecuteAndIfNecessaryTraceCommand("Job query", xmlElement.OwnerDocument);
	}

	public int CreateJobActivity(JobActivity jobActivity_)
	{
		return CreateJobActivity(jobActivity_, JobActivityCreationType_Enum.jactNoSeries);
	}

	public int CreateJobActivitySeriesMember(JobActivity jobActivity_, int existingJobActivitySeriesId_)
	{
		return CreateJobActivity(jobActivity_, JobActivityCreationType_Enum.jactExistingSeries, existingJobActivitySeriesId_);
	}

	public int CreateJobActivitySeries(JobActivity jobActivity_, int newSeriesLength_, string newSeriesName_ = "")
	{
		return CreateJobActivity(jobActivity_, JobActivityCreationType_Enum.jactNewSeries, 0, newSeriesLength_, newSeriesName_);
	}

	private int CreateJobActivity(JobActivity jobActivity_, JobActivityCreationType_Enum jobCreationType_, int existingSeriesId_ = 0, int newSeriesLength_ = 0, string newSeriesName_ = "")
	{
		XmlElement xmlElement = CreateCommandDocument("jobActivityCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "job", jobActivity_.JobId), "jobActivity");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "activityType", jobActivity_.JobActivityTypeId);
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "status", jobActivity_.JobActivityStatusId);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "startDate", jobActivity_.StartDate.HasValue ? jobActivity_.StartDate.Value.ToString("yyyy-MM-dd") : "");
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "schedTime", jobActivity_.ScheduledTime.HasValue ? jobActivity_.ScheduledTime.Value.ToString("HH:mm") : "");
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "duration", jobActivity_.ScheduledDuration.HasValue ? jobActivity_.ScheduledDuration.Value.ToString("HH:mm") : "");
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "notes", jobActivity_.Notes);
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, jobActivity_.CustomFieldValues, "jobActivity");
		if (jobActivity_.Assignees != null)
		{
			AppendAssigneesForCreateOrUpdate(xmlElement2, jobActivity_.Assignees);
		}
		if (jobActivity_.JobPhases != null)
		{
			AppendJobPhasesForCreateOrUpdate(xmlElement2, jobActivity_.JobPhases);
		}
		switch (jobCreationType_)
		{
		case JobActivityCreationType_Enum.jactExistingSeries:
			modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobActivitySeries"), "existing", existingSeriesId_);
			break;
		case JobActivityCreationType_Enum.jactNewSeries:
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobActivitySeries"), "new", newSeriesLength_, "dayCount"), "name", newSeriesName_);
			break;
		}
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Job Activity create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("jobActivityCreate/job/jobActivity");
		jobActivity_.JobActivityId = int.Parse(xmlElement3.GetAttribute("id"));
		jobActivity_.ClearUpdateFlags();
		return jobActivity_.JobActivityId;
	}

	public void UpdateJobActivity(JobActivity jobActivity_)
	{
		UpdateJobActivity(jobActivity_, JobActivityUpdateType_Enum.jautNoSeriesChanges);
	}

	public void UpdateJobActivityAndCreateSeries(JobActivity jobActivity_, int seriesLength_, string seriesName_ = "")
	{
		UpdateJobActivity(jobActivity_, JobActivityUpdateType_Enum.jautNewSeries, seriesLength_, seriesName_);
	}

	public void UpdateJobActivityAndRemoveFromSeries(JobActivity jobActivity_)
	{
		UpdateJobActivity(jobActivity_, JobActivityUpdateType_Enum.jautRemoveFromSeries);
	}

	public void UpdateJobActivityAndAttachToSeries(JobActivity jobActivity_, int jobActivitySeriesId_)
	{
		UpdateJobActivity(jobActivity_, JobActivityUpdateType_Enum.jautExistingSeries, 0, "", jobActivitySeriesId_);
	}

	public void UpdateJobActivityAndExtendCurrentSeries(JobActivity jobActivity_, int additionalDays_)
	{
		UpdateJobActivity(jobActivity_, JobActivityUpdateType_Enum.jautExtendSeries, additionalDays_);
	}

	private void UpdateJobActivity(JobActivity jobActivity_, JobActivityUpdateType_Enum seriesUpdateType_, int dayCount_ = 0, string newSeriesName_ = "", int existingSeriesId_ = 0)
	{
		XmlElement xmlElement = CreateCommandDocument("jobActivityUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobActivity", jobActivity_.JobActivityId);
		if (jobActivity_.ModifiedJobActivityStatus)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "status", jobActivity_.JobActivityStatusId);
		}
		if (jobActivity_.ModifiedStartDate)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "startDate", jobActivity_.StartDate.HasValue ? jobActivity_.StartDate.Value.ToString("yyyy-MM-dd") : "", includeEmptyTextElements_: true);
		}
		if (jobActivity_.ModifiedScheduledTime)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "schedTime", jobActivity_.ScheduledTime.HasValue ? jobActivity_.ScheduledTime.Value.ToString("HH:mm") : "", includeEmptyTextElements_: true);
		}
		if (jobActivity_.ModifiedScheduledDuration)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "duration", jobActivity_.ScheduledDuration.HasValue ? jobActivity_.ScheduledDuration.Value.ToString("HH:mm") : "", includeEmptyTextElements_: true);
		}
		if (jobActivity_.ModifiedNotes)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "notes", jobActivity_.Notes, includeEmptyTextElements_: true);
		}
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, jobActivity_.CustomFieldValues, "jobActivity");
		if (jobActivity_.ModifiedAssignees)
		{
			AppendAssigneesForCreateOrUpdate(xmlElement2, jobActivity_.Assignees);
		}
		if (jobActivity_.JobPhases.Modified)
		{
			AppendJobPhasesForCreateOrUpdate(xmlElement2, jobActivity_.JobPhases);
		}
		switch (seriesUpdateType_)
		{
		case JobActivityUpdateType_Enum.jautExistingSeries:
			modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobActivitySeries"), "existing", existingSeriesId_);
			break;
		case JobActivityUpdateType_Enum.jautExtendSeries:
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobActivitySeries"), "extension").SetAttribute("additionalDayCount", dayCount_.ToString());
			break;
		case JobActivityUpdateType_Enum.jautNewSeries:
		{
			XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobActivitySeries"), "new");
			xmlElement3.SetAttribute("dayCount", dayCount_.ToString());
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement3, "name", newSeriesName_);
			break;
		}
		case JobActivityUpdateType_Enum.jautRemoveFromSeries:
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobActivitySeries"), "none");
			break;
		}
		ExecuteAndIfNecessaryTraceCommand("Job Activity update", xmlElement.OwnerDocument);
		jobActivity_.ClearUpdateFlags();
	}

	private void AppendJobPhasesForCreateOrUpdate(XmlElement parentElement_, JobPhaseContainer jobPhases_, bool forceIncludeJobPhasesElement_ = false)
	{
		if (!forceIncludeJobPhasesElement_ && jobPhases_ != null)
		{
			forceIncludeJobPhasesElement_ = jobPhases_.Modified;
		}
		if (!forceIncludeJobPhasesElement_)
		{
			return;
		}
		XmlElement xmlElement = modInternalXMLHelperFunctions.AppendElement(parentElement_, "jobPhases");
		if (jobPhases_ == null)
		{
			return;
		}
		if (jobPhases_.All)
		{
			xmlElement.SetAttribute("all", "1");
			return;
		}
		foreach (JobPhase item in jobPhases_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobPhase", item.JobPhaseId);
		}
	}

	public int CreateJobPhase(JobPhase jobPhase_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobPhaseCreate");
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobPhase", jobPhase_.JobId, "jobId"), "name", jobPhase_.JobPhaseName, includeEmptyTextElements_: true);
		XmlElement xmlElement2 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Job Phase create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("jobPhaseCreate/jobPhase");
		jobPhase_.JobPhaseId = int.Parse(xmlElement2.GetAttribute("id"));
		jobPhase_.ClearUpdateFlags();
		return jobPhase_.JobPhaseId;
	}

	public void DeleteJobPhase(int jobPhaseId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobPhaseDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobPhase", jobPhaseId_);
		ExecuteAndIfNecessaryTraceCommand("Job Phase delete", xmlElement.OwnerDocument);
	}

	public void UpdateJobPhase(JobPhase jobPhase_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobPhaseUpdate");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobPhase", jobPhase_.JobPhaseId);
		if (jobPhase_.ModifiedJobPhaseName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(parentNode_, "name", jobPhase_.JobPhaseName, includeEmptyTextElements_: true);
		}
		ExecuteAndIfNecessaryTraceCommand("Job Phase update", xmlElement.OwnerDocument);
		jobPhase_.ClearUpdateFlags();
	}

	public void ReorderJobPhases(IEnumerable<int> jobPhaseIds_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobPhaseReorder");
		foreach (int item in jobPhaseIds_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobPhase", item);
		}
		if (xmlElement.SelectSingleNode("*") != null)
		{
			ExecuteAndIfNecessaryTraceCommand("Job Phase reorder", xmlElement.OwnerDocument);
		}
	}

	public int CreateJobForm(JobForm jobForm_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobFormCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "job", jobForm_.JobId), "jobForm");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "formTemplate", jobForm_.FormTemplateId);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", jobForm_.JobFormName);
		AddFormFieldsForUpdateOrCreate(xmlElement2, jobForm_.FormTemplateId, jobForm_.FieldValues);
		if (jobForm_.JobPhases != null)
		{
			AppendJobPhasesForCreateOrUpdate(xmlElement2, jobForm_.JobPhases);
		}
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Job Form create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("jobFormCreate/job/jobForm");
		jobForm_.JobFormId = int.Parse(xmlElement3.GetAttribute("id"));
		jobForm_.ClearUpdateFlags();
		return jobForm_.JobFormId;
	}

	public void UpdateJobForm(JobForm jobForm_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobFormUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobForm", jobForm_.JobFormId);
		if (jobForm_.ModifiedJobFormName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", jobForm_.JobFormName);
		}
		if (jobForm_.JobPhases != null && jobForm_.JobPhases.Modified)
		{
			AppendJobPhasesForCreateOrUpdate(xmlElement2, jobForm_.JobPhases);
		}
		AddFormFieldsForUpdateOrCreate(xmlElement2, jobForm_.FormTemplateId, jobForm_.FieldValues);
		ExecuteAndIfNecessaryTraceCommand("Job Form update", xmlElement.OwnerDocument);
		jobForm_.ClearUpdateFlags();
	}

	public void ConvertJob(int jobId_, int processId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobConvert");
		modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "job", jobId_), "process", processId_);
		ExecuteAndIfNecessaryTraceCommand("Convert Job", xmlElement.OwnerDocument);
	}

	public int CreateJob(Job job_)
	{
		return CreateJob(job_, allowDuplicates_: false, null, useSpecifiedCreationDate_: false);
	}

	public int CreateJob(Job job_, bool allowDuplicates_)
	{
		return CreateJob(job_, allowDuplicates_, null, useSpecifiedCreationDate_: false);
	}

	public int CreateJob(Job job_, bool allowDuplicates_, int? jobTemplateId_)
	{
		return CreateJob(job_, allowDuplicates_, jobTemplateId_, useSpecifiedCreationDate_: false);
	}

	public int CreateJob(Job job_, bool allowDuplicates_, int? jobTemplateId_, bool useSpecifiedCreationDate_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobCreate");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "process", job_.ProcessId);
		if (allowDuplicates_)
		{
			modInternalXMLHelperFunctions.AppendElement(xmlElement, "allowDuplicateJob");
		}
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "account", job_.AccountId);
		if (modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement, "name", job_.JobName) == null)
		{
			throw new APIException(null, "Missing Job Name when creating a job.", APIException.APIErrorCodes_Enum.GeneralException);
		}
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "salesperson", job_.SalespersonName, includeEmptyTextElements_: true);
		if (job_.SalespersonId.HasValue)
		{
			xmlElement2.SetAttribute("id", job_.SalespersonId.ToString());
		}
		if (useSpecifiedCreationDate_)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement, "creationDate", job_.CreationDate.ToString("yyyy-MM-dd"));
		}
		modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement, "notes", job_.Notes);
		if (jobTemplateId_ > -1)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobTemplate", $"{jobTemplateId_}");
		}
		AppendAddressNodeIfNecessary(xmlElement, job_.Address, "address", includeEmptyAddressFields_: false);
		if (job_.Contacts != null)
		{
			AddJobContactsForCreateOrUpdate(xmlElement, job_.Contacts);
		}
		AddCustomFieldsUpdateOrCreationElement(xmlElement, job_.CustomFieldValues, "job");
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Job Create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("jobCreate/job");
		job_.JobId = int.Parse(xmlElement3.GetAttribute("id"));
		job_.ClearUpdateFlags();
		return job_.JobId;
	}

	public void UpdateJob(Job job_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "job");
		xmlElement2.SetAttribute("id", job_.JobId.ToString());
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, job_.CustomFieldValues, "job");
		if (job_.ModifiedCreationDate)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "creationDate", job_.CreationDate.ToString("yyyy-MM-dd"), includeEmptyTextElements_: true);
		}
		if (job_.ModifiedJobName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", job_.JobName, includeEmptyTextElements_: true);
		}
		if (job_.ModifiedNotes)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "notes", job_.Notes, includeEmptyTextElements_: true);
		}
		if (job_.ModifiedSalesperson)
		{
			XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "salesperson", job_.SalespersonName, includeEmptyTextElements_: true);
			if (job_.SalespersonId.HasValue)
			{
				xmlElement3.SetAttribute("id", job_.SalespersonId.ToString());
			}
		}
		if (job_.ModifiedAddress)
		{
			AppendAddressNodeIfNecessary(xmlElement2, job_.Address, "address", includeEmptyAddressFields_: true);
		}
		if (job_.Contacts.Modified)
		{
			AddJobContactsForCreateOrUpdate(xmlElement2, job_.Contacts);
		}
		ExecuteAndIfNecessaryTraceCommand("Job update", xmlElement.OwnerDocument);
		job_.ClearUpdateFlags();
	}

	public void MoveJobToAccount(int jobId_, int accountId_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobAccountUpdate");
		xmlElement.SetAttribute("jobId", $"{jobId_}");
		xmlElement.SetAttribute("accountId", $"{accountId_}");
		ExecuteAndIfNecessaryTraceCommand("Move Job To Account", xmlElement.OwnerDocument);
	}

	private void AddFormFieldsForUpdateOrCreate(XmlElement parentElement_, int formTemplateId_, JobFormFieldValueContainer formFieldValues_)
	{
		if (formFieldValues_ == null || !formFieldValues_.Modified)
		{
			return;
		}
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(parentElement_, "formFieldValues");
		foreach (JobFormFieldValue item in formFieldValues_)
		{
			if (item.ModifiedValue)
			{
				XmlElement xmlElement = modInternalXMLHelperFunctions.AppendObjectAsTextElement(modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "formFieldValue", item.JobFormFieldId), "value", item.FieldValue, includeEmptyTextElements_: true);
				if (item.FieldValueId.HasValue)
				{
					xmlElement.SetAttribute("id", $"{item.FieldValueId}");
				}
			}
		}
	}

	public void DeleteJob(int jobId_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobDelete");
		ValidateConnected();
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "job", jobId_);
		ExecuteAndIfNecessaryTraceCommand("Job delete", xmlElement.OwnerDocument);
	}

	public void DeleteJobForm(int jobFormId_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobFormDelete");
		ValidateConnected();
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobForm", jobFormId_);
		ExecuteAndIfNecessaryTraceCommand("Job Form delete", xmlElement.OwnerDocument);
	}

	public void DeleteJobActivity(int jobActivityId_)
	{
		XmlElement xmlElement = CreateCommandDocument("jobActivityDelete");
		ValidateConnected();
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobActivity", jobActivityId_);
		ExecuteAndIfNecessaryTraceCommand("Job Activity delete", xmlElement.OwnerDocument);
	}

	public JobForm GetJobForm(int jobFormId_, bool includeJobPhases_, GetJobForm_FieldInclusionType_Enum fieldIndicator_ = GetJobForm_FieldInclusionType_Enum.NoFields)
	{
		List<JobForm> jobFormsOrJobForm = GetJobFormsOrJobForm(0, jobFormId_, useJobId_: false, includeJobPhases_, fieldIndicator_);
		if (jobFormsOrJobForm.Count == 0)
		{
			return null;
		}
		return jobFormsOrJobForm[0];
	}

	public List<JobForm> GetJobForms(int jobId_, bool includeJobPhases_, GetJobForm_FieldInclusionType_Enum fieldIndicator_ = GetJobForm_FieldInclusionType_Enum.NoFields)
	{
		return GetJobFormsOrJobForm(jobId_, 0, useJobId_: true, includeJobPhases_, fieldIndicator_);
	}

	private List<JobForm> GetJobFormsOrJobForm(int jobId_, int jobFormId_, bool useJobId_, bool includeJobPhases_, GetJobForm_FieldInclusionType_Enum fieldIndicator_ = GetJobForm_FieldInclusionType_Enum.NoFields)
	{
		List<JobForm> list = new List<JobForm>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobFormQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (useJobId_)
		{
			modInternalXMLHelperFunctions.AppendElement(parentNode_, "job").SetAttribute("id", jobId_.ToString());
		}
		else
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "jobForm", jobFormId_);
		}
		XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElements(parentNode_2, new string[2] { "name", "job" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "formTemplate"), "name");
		if (includeJobPhases_)
		{
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "jobPhase"), "all");
		}
		bool flag = true;
		switch (fieldIndicator_)
		{
		case GetJobForm_FieldInclusionType_Enum.ExcludeEmptyFields:
			modInternalXMLHelperFunctions.AppendElement(parentNode_, "excludeEmptyFields");
			break;
		default:
			fieldIndicator_ = GetJobForm_FieldInclusionType_Enum.NoFields;
			flag = false;
			break;
		case GetJobForm_FieldInclusionType_Enum.AllFields:
			break;
		}
		if (flag)
		{
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "formField"), new string[3] { "name", "value", "dataType" });
		}
		XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("Job Form query", xmlElement.OwnerDocument);
		string text = null;
		text = ((!useJobId_) ? "jobFormQuery/jobForm" : "jobFormQuery/job/jobForms/jobForm");
		foreach (XmlElement item in xmlDocument.DocumentElement.SelectNodes(text))
		{
			int jobFormId_2 = int.Parse(item.GetAttribute("id"));
			XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(item, "formTemplate");
			int formTemplateId = int.Parse(childElementIfThere.GetAttribute("id"));
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name");
			int num = Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(item, "job").GetAttribute("id"));
			JobForm jobForm = new JobForm(jobFormId_2)
			{
				JobFormName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "name"),
				JobId = num,
				FormTemplateId = formTemplateId,
				FormTemplateName = textOfChildIfThere
			};
			if (flag)
			{
				foreach (XmlElement item2 in item.SelectNodes("formFields/jobField"))
				{
					int jobFormFieldId_ = int.Parse(item2.GetAttribute("id"));
					string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "name");
					XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(item2, "value");
					string fieldValue_ = "";
					int? fieldValueId_ = null;
					if (childElementIfThere2 != null)
					{
						fieldValue_ = CanonicalizeMultiLineTextFromResponse(childElementIfThere2.InnerText);
						if (childElementIfThere2.HasAttribute("id"))
						{
							fieldValueId_ = int.Parse(childElementIfThere2.GetAttribute("id"));
						}
					}
					string attribute = item2.GetAttribute("dataType");
					jobForm.FieldValues.AddJobFormFieldValue(jobFormFieldId_, textOfChildIfThere2, attribute).SetFieldIdAndValue(fieldValueId_, fieldValue_);
				}
			}
			if (!GetJobPhasesIfThere(jobForm.JobPhases, item, num))
			{
				jobForm.JobPhases = null;
			}
			jobForm.ClearUpdateFlags();
			list.Add(jobForm);
		}
		return list;
	}

	private static void AppendProcessesToFilter(XmlElement filterElement_, IEnumerable<int> processIds_)
	{
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(filterElement_, "processes");
		foreach (int item in processIds_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "process", item);
		}
	}

	private List<JobActivityType> GetJobActivityTypes(IEnumerable<int> processIds_)
	{
		List<JobActivityType> list = new List<JobActivityType>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("activityTypeQuery");
		if (processIds_ != null)
		{
			AppendProcessesToFilter(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), processIds_);
		}
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[3] { "processes", "name", "description" });
		foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Job Activity Type query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("activityTypeQuery/activityType"))
		{
			JobActivityType item = new JobActivityType(int.Parse(item2.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "description"), "1" == item2.GetAttribute("isInactive"), BuildProcessIdList(modInternalXMLHelperFunctions.GetChildElementIfThere(item2, "processes")));
			list.Add(item);
		}
		return list;
	}

	public List<JobActivityType> GetJobActivityTypes(int processId_)
	{
		return GetJobActivityTypes(new int[1] { processId_ });
	}

	public List<JobActivityType> GetJobActivityTypes()
	{
		return GetJobActivityTypes(null);
	}

	internal static List<int> BuildProcessIdList(XmlElement processesElement_)
	{
		List<int> list = new List<int>();
		if (processesElement_ != null)
		{
			foreach (XmlElement item2 in processesElement_.SelectNodes("process"))
			{
				int item = int.Parse(item2.GetAttribute("id"));
				list.Add(item);
			}
		}
		return list;
	}

	public List<JobActivityStatus> GetJobActivityStatuses()
	{
		List<JobActivityStatus> list = new List<JobActivityStatus>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobActivityStatusQuery");
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[8] { "name", "abbreviation", "seqNum", "type", "isInactive", "displayColor", "confirmTimeChange", "validForAppointments" });
		foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Job Activity Status query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("jobActivityStatusQuery/jobActivityStatus"))
		{
			JobActivityStatus.JobActivityStatusType_Enum jobActivityStatusType_Enum = JobActivityStatus.JobActivityStatusType_Enum.AutoSchedule;
			string attribute = item2.GetAttribute("type");
			jobActivityStatusType_Enum = attribute switch
			{
				"Auto-Schedule" => JobActivityStatus.JobActivityStatusType_Enum.AutoSchedule, 
				"Active" => JobActivityStatus.JobActivityStatusType_Enum.Active, 
				"Complete" => JobActivityStatus.JobActivityStatusType_Enum.Complete, 
				"Canceled" => JobActivityStatus.JobActivityStatusType_Enum.Canceled, 
				_ => throw new Exception("Unknown job activity status type:  \"" + attribute + "\"."), 
			};
			bool confirmTimeChange_ = "1" == item2.GetAttribute("confirmTimeChange");
			bool validForAppointments_ = "1" == item2.GetAttribute("validForAppointments");
			JobActivityStatus item = new JobActivityStatus(int.Parse(item2.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "abbreviation"), "1" == item2.GetAttribute("isInactive"), int.Parse(item2.GetAttribute("seqNum")), jobActivityStatusType_Enum, modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "displayColor"), confirmTimeChange_, validForAppointments_);
			list.Add(item);
		}
		return list;
	}

	public Dictionary<int, JobActivityStatus> GetJobActivityStatusIdMap()
	{
		Dictionary<int, JobActivityStatus> dictionary = new Dictionary<int, JobActivityStatus>();
		foreach (JobActivityStatus jobActivityStatus in GetJobActivityStatuses())
		{
			dictionary.Add(jobActivityStatus.JobActivityStatusId, jobActivityStatus);
		}
		return dictionary;
	}

	public Dictionary<string, JobActivityStatus> GetJobActivityStatusNameMap()
	{
		Dictionary<string, JobActivityStatus> dictionary = new Dictionary<string, JobActivityStatus>();
		foreach (JobActivityStatus jobActivityStatus in GetJobActivityStatuses())
		{
			dictionary.Add(jobActivityStatus.JobActivityStatusName, jobActivityStatus);
		}
		return dictionary;
	}

	public JobActivity GetJobActivity(int jobActivityId_, bool includeJobPhases_, bool includeJobActivitySeriesMember_)
	{
		List<JobActivity> jobActivitiesByJobOrActivityOrSeries = GetJobActivitiesByJobOrActivityOrSeries(0, jobActivityId_, 0, useJob_: false, useJobActivitySeries_: false, includeJobPhases_, includeJobActivitySeriesMember_);
		if (jobActivitiesByJobOrActivityOrSeries.Count == 0)
		{
			return null;
		}
		return jobActivitiesByJobOrActivityOrSeries[0];
	}

	public List<JobActivity> GetJobActivities(int jobId_, bool includeJobPhases_, bool includeJobActivitySeriesMember_)
	{
		return GetJobActivitiesByJobOrActivityOrSeries(jobId_, 0, 0, useJob_: true, useJobActivitySeries_: false, includeJobPhases_, includeJobActivitySeriesMember_);
	}

	public List<JobActivity> GetJobActivitiesForSeries(int jobActivitySeriesId_, bool includeJobPhases_, bool includeJobActivitySeriesMember_)
	{
		return GetJobActivitiesByJobOrActivityOrSeries(0, 0, jobActivitySeriesId_, useJob_: false, useJobActivitySeries_: true, includeJobPhases_, includeJobActivitySeriesMember_);
	}

	private List<JobActivity> GetJobActivitiesByJobOrActivityOrSeries(int jobId_, int jobActivityId_, int jobActivitySeriesId_, bool useJob_, bool useJobActivitySeries_, bool includeJobPhases_, bool includeJobActivitySeriesMember_)
	{
		List<JobActivity> list = new List<JobActivity>();
		XmlElement xmlElement = CreateCommandDocument("jobActivityQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (useJob_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "job", jobId_);
		}
		else if (useJobActivitySeries_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "jobActivitySeries", jobActivitySeriesId_);
		}
		else
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "jobActivity", jobActivityId_);
		}
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "activityType"), "name");
		modInternalXMLHelperFunctions.AppendElements(xmlElement2, new string[4] { "startDate", "schedTime", "duration", "notes" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "assignee"), "all");
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "status"), new string[1] { "name" });
		modInternalXMLHelperFunctions.AppendElement(xmlElement2, "job");
		if (includeJobPhases_)
		{
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobPhase"), "all");
		}
		if (includeJobActivitySeriesMember_)
		{
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobActivitySeries"), new string[3] { "name", "length", "seqNum" });
		}
		AddObjectCustomFieldIncludeElements(xmlElement2, "jobActivity");
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Job Activity query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("jobActivityQuery/jobActivity"))
		{
			XmlElement obj = (XmlElement)item.SelectSingleNode("status");
			int jobActivityStatusId_ = int.Parse(obj.GetAttribute("id"));
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(obj, "name");
			DateTime? startDate = null;
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "startDate");
			if (textOfChildIfThere2.Length > 0)
			{
				startDate = ParseDate(textOfChildIfThere2);
			}
			DateTime? scheduledTime = null;
			string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "schedTime");
			if (textOfChildIfThere3.Length > 0)
			{
				scheduledTime = ParseHMTime(textOfChildIfThere3);
			}
			DateTime? scheduledDuration = null;
			string textOfChildIfThere4 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "duration");
			if (textOfChildIfThere4.Length > 0)
			{
				scheduledDuration = ParseHMTime(textOfChildIfThere4);
			}
			int num = Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(item, "job").GetAttribute("id"));
			int jobActivityId_2 = int.Parse(item.GetAttribute("id"));
			XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(item, "activityType");
			JobActivitySeriesMember jobActivitySeriesMember = null;
			XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(item, "jobActivitySeries");
			if (childElementIfThere2 != null)
			{
				jobActivitySeriesMember = new JobActivitySeriesMember(int.Parse(childElementIfThere2.GetAttribute("id")), int.Parse(childElementIfThere2.GetAttribute("seqNum")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere2, "name"), int.Parse(childElementIfThere2.GetAttribute("length")));
			}
			JobActivity jobActivity = new JobActivity(jobActivityId_2)
			{
				JobId = num,
				JobActivityTypeId = int.Parse(childElementIfThere.GetAttribute("id")),
				JobActivityTypeName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name"),
				StartDate = startDate,
				ScheduledTime = scheduledTime,
				ScheduledDuration = scheduledDuration,
				Notes = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "notes")),
				JobActivitySeriesMember = jobActivitySeriesMember,
				CustomFieldValues = GetCustomFieldValuesForObject(item),
				Assignees = new AssigneeContainer()
			};
			foreach (XmlElement item2 in item.SelectNodes("assignees/assignee"))
			{
				jobActivity.Assignees.Add(GetAssigneeFromAssigneeElement(item2));
			}
			jobActivity.SetJobActivityStatusIdAndName(jobActivityStatusId_, textOfChildIfThere);
			GetJobPhasesIfThere(jobActivity.JobPhases, item, num);
			jobActivity.ClearUpdateFlags();
			list.Add(jobActivity);
		}
		return list;
	}

	internal bool GetJobPhasesIfThere(JobPhaseContainer jobPhases_, XmlElement jobPhasesParentElement_, int jobId_)
	{
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(jobPhasesParentElement_, "jobPhases");
		if (childElementIfThere != null)
		{
			jobPhases_.All = "1" == childElementIfThere.GetAttribute("all");
			if (!jobPhases_.All)
			{
				foreach (XmlElement item in childElementIfThere.SelectNodes("jobPhase"))
				{
					jobPhases_.Add(GetJobPhaseFromJobPhaseElement(item, jobId_));
				}
			}
			return true;
		}
		return false;
	}

	private JobPhase GetJobPhaseFromJobPhaseElement(XmlElement jobPhaseElement_, int jobId_)
	{
		JobPhase jobPhase = null;
		if (jobPhaseElement_ != null)
		{
			jobPhase = new JobPhase(int.Parse(jobPhaseElement_.GetAttribute("id")))
			{
				JobPhaseName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(jobPhaseElement_, "name"),
				SeqNum = int.Parse(jobPhaseElement_.GetAttribute("seqNum")),
				JobId = jobId_
			};
			jobPhase.ClearUpdateFlags();
		}
		return jobPhase;
	}

	public JobActivitySeries GetJobActivitySeries(int jobActivitySeriesId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobActivitySeriesQuery");
		modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "jobActivitySeries", jobActivitySeriesId_);
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElements(parentNode_, new string[4] { "name", "length", "workDays", "schedTime" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_, "job"), "name");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_, "activityType"), "name");
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(ExecuteAndIfNecessaryTraceCommand("Job activity series query", xmlElement.OwnerDocument).DocumentElement, "jobActivitySeriesQuery/jobActivitySeries");
		if (childElementIfThere == null)
		{
			return null;
		}
		XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(childElementIfThere, "activityType");
		int id_ = int.Parse(childElementIfThere.GetAttribute("id"));
		int activityTypeId_ = int.Parse(childElementIfThere2.GetAttribute("id"));
		int workDays_ = int.Parse(childElementIfThere.GetAttribute("workDays"));
		int length_ = int.Parse(childElementIfThere.GetAttribute("length"));
		DateTime? scheduledTime_ = ParseHMTime(modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "schedTime"));
		XmlElement childElementIfThere3 = modInternalXMLHelperFunctions.GetChildElementIfThere(childElementIfThere, "job");
		return new JobActivitySeries(jobId_: int.Parse(childElementIfThere3.GetAttribute("id")), id_: id_, name_: modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name"), jobName_: modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere3, "name"), activityTypeId_: activityTypeId_, activityTypeName_: modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere2, "name"), workDays_: workDays_, length_: length_, scheduledTime_: scheduledTime_);
	}

	public void DeleteJobActivitySeries(int jobActivitySeriesId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobActivitySeriesDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "jobActivitySeries", jobActivitySeriesId_);
		ExecuteAndIfNecessaryTraceCommand("Delete Job Activity Series", xmlElement.OwnerDocument);
	}

	public void UpdateJobActivitySeries(JobActivitySeries jobActivitySeries_, IEnumerable<int> orderedJobActivityIds_ = null)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobActivitySeriesUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "jobActivitySeries");
		xmlElement2.SetAttribute("id", jobActivitySeries_.JobActivitySeriesId.ToString());
		if (jobActivitySeries_.ModifiedJobActivitySeriesName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", jobActivitySeries_.JobActivitySeriesName, includeEmptyTextElements_: true);
		}
		if (jobActivitySeries_.ModifiedWorkDays)
		{
			xmlElement2.SetAttribute("workDays", Convert.ToInt32(jobActivitySeries_.WorkDays).ToString());
		}
		if (jobActivitySeries_.ModifiedScheduledTime)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "schedTime", jobActivitySeries_.ScheduledTime?.ToString("HH:mm"), includeEmptyTextElements_: true);
		}
		if (orderedJobActivityIds_ != null)
		{
			XmlElement xmlElement3 = null;
			foreach (int item in orderedJobActivityIds_)
			{
				if (xmlElement3 == null)
				{
					xmlElement3 = modInternalXMLHelperFunctions.AppendElement(xmlElement2, "orderedJobActivities");
				}
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement3, "jobActivity", item);
			}
		}
		ExecuteAndIfNecessaryTraceCommand("Delete Job Activity Series", xmlElement.OwnerDocument);
		jobActivitySeries_.ClearUpdateFlags();
	}

	public void ReorderJobActivitiesInSeries(int jobActivitySeriesId_, IEnumerable<int> orderedJobActivityIds_)
	{
		UpdateJobActivitySeries(new JobActivitySeries(jobActivitySeriesId_), orderedJobActivityIds_);
	}

	public JTProcess GetProcess(int processId_)
	{
		List<JTProcess> processes = GetProcesses(new int[1] { processId_ });
		if (processes.Count == 0)
		{
			return null;
		}
		return processes[0];
	}

	public List<JTProcess> GetProcesses()
	{
		return GetProcesses(null);
	}

	private List<JTProcess> GetProcesses(IEnumerable<int> processIds_)
	{
		List<JTProcess> list = new List<JTProcess>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("processQuery");
		if (processIds_ != null)
		{
			flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in processIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "process", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[4] { "name", "seqNum", "pluralName", "isInactive" });
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Process query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("processQuery/process"))
			{
				list.Add(GetProcessFromProcessElement(item2));
			}
		}
		return list;
	}

	private JTProcess GetProcessFromProcessElement(XmlElement processElement_)
	{
		return new JTProcess(int.Parse(processElement_.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(processElement_, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(processElement_, "pluralName"), "1" == processElement_.GetAttribute("isInactive"), int.Parse(processElement_.GetAttribute("seqNum")));
	}

	private void AddJobContactsForCreateOrUpdate(XmlElement parentElement_, IEnumerable<JobContact> contacts_)
	{
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(parentElement_, "jobContacts");
		if (contacts_ == null)
		{
			return;
		}
		foreach (JobContact item in contacts_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "jobContact", item.ContactId);
		}
	}

	public List<JobTemplate> GetJobTemplates(int processId_ = 1)
	{
		List<JobTemplate> list = null;
		list = new List<JobTemplate>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("jobTemplateQuery");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "process").SetAttribute("id", processId_.ToString());
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "name");
		foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Job Template query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("jobTemplateQuery/jobTemplate"))
		{
			JobTemplate item = new JobTemplate(int.Parse(item2.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "name"));
			list.Add(item);
		}
		return list;
	}

	public PageView GetPageView(int pageViewId_)
	{
		List<PageView> pageViews = GetPageViews(new int[1] { pageViewId_ });
		if (pageViews.Count > 0)
		{
			return pageViews[0];
		}
		return null;
	}

	public List<PageView> GetPageViews()
	{
		return GetPageViews(new PageViewFilter());
	}

	public List<PageView> GetPageViews(IEnumerable<int> pageViewIds_)
	{
		if (pageViewIds_ == null)
		{
			pageViewIds_ = new int[0];
		}
		return GetPageViews(new PageViewFilter(pageViewIds_, null, null));
	}

	public List<PageView> GetPageViewsOfPage(PageView.Page_Enum page_)
	{
		return GetPageViewsOfPages(new PageView.Page_Enum[1] { page_ });
	}

	public List<PageView> GetPageViewsOfPages(IEnumerable<PageView.Page_Enum> pages_)
	{
		if (pages_ == null)
		{
			pages_ = new PageView.Page_Enum[0];
		}
		return GetPageViews(new PageViewFilter(pages_, null));
	}

	public List<PageView> GetPageViews(PageViewFilter pageViewFilter_)
	{
		List<PageView> list = new List<PageView>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("pageViewQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (pageViewFilter_.PageViewIds != null)
		{
			flag = true;
			foreach (int pageViewId in pageViewFilter_.PageViewIds)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "pageView", pageViewId);
			}
		}
		if (pageViewFilter_.PageViewTypes != null)
		{
			flag = true;
			XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "includedPageViewTypes");
			foreach (PageView.PageViewType_Enum pageViewType in pageViewFilter_.PageViewTypes)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "pageViewType", PageView.GetViewTypeName(pageViewType));
			}
		}
		if (pageViewFilter_.Pages != null)
		{
			flag = true;
			XmlElement parentNode_3 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "includedPages");
			foreach (PageView.Page_Enum page in pageViewFilter_.Pages)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_3, "page", PageView.GetPageName(page));
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("PageView query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("pageViewQuery/pageView"))
			{
				list.Add(GetPageViewFromPageViewElement(item));
			}
		}
		return list;
	}

	private PageView GetPageViewFromPageViewElement(XmlElement pageViewElement_)
	{
		int pageViewId_ = int.Parse(pageViewElement_.GetAttribute("id"));
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(pageViewElement_, "name");
		string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(pageViewElement_, "page");
		PageView obj = new PageView(pageViewType_: PageView.GetViewTypeFromName(modInternalXMLHelperFunctions.GetTextOfChildIfThere(pageViewElement_, "pageViewType")), pageViewId_: pageViewId_, pageViewName_: textOfChildIfThere, page_: PageView.GetPageFromName(textOfChildIfThere2));
		obj.ClearUpdateFlags();
		return obj;
	}

	private void AppendViewFilterIfNecessary(XmlElement filterElement_, int? viewId_)
	{
		if (viewId_.HasValue)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(filterElement_, "pageView", viewId_.Value);
		}
	}

	public PurchaseProduct GetPurchaseProduct(int purchaseProductId_)
	{
		List<PurchaseProduct> purchaseProducts = GetPurchaseProducts(new int[1] { purchaseProductId_ });
		if (purchaseProducts.Count == 0)
		{
			return null;
		}
		return purchaseProducts[0];
	}

	public List<PurchaseProduct> GetPurchaseProducts(IEnumerable<int> purchaseProductIds_)
	{
		return (List<PurchaseProduct>)GetPurchaseOrSellProducts(purchaseProductIds_, purchaseProducts_: true);
	}

	public List<PurchaseProduct> GetPurchaseProducts()
	{
		return GetPurchaseProducts(null);
	}

	public SellProduct GetSellProduct(int sellProductId_)
	{
		List<SellProduct> sellProducts = GetSellProducts(new int[1] { sellProductId_ });
		if (sellProducts.Count == 0)
		{
			return null;
		}
		return sellProducts[0];
	}

	public List<SellProduct> GetSellProducts(IEnumerable<int> sellProductIds_)
	{
		return (List<SellProduct>)GetPurchaseOrSellProducts(sellProductIds_, purchaseProducts_: false);
	}

	public List<SellProduct> GetSellProducts()
	{
		return GetSellProducts(null);
	}

	private object GetPurchaseOrSellProducts(IEnumerable<int> productIds_, bool purchaseProducts_)
	{
		List<PurchaseProduct> list = null;
		List<SellProduct> list2 = null;
		string text = (purchaseProducts_ ? "purchase" : "sell").ToString();
		if (purchaseProducts_)
		{
			list = new List<PurchaseProduct>();
		}
		else
		{
			list2 = new List<SellProduct>();
		}
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument($"{text}ProductQuery");
		if (productIds_ != null)
		{
			flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in productIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, $"{text}Product", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "productFamily"), "name");
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "productLine"), "name");
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "unitOfMeasure"), "name");
			modInternalXMLHelperFunctions.AppendElements(parentNode_2, new string[3] { "name", "variantCount", "isInactive" });
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "productAttributeType"), new string[3] { "name", "isCustomSort", "description" });
			if (purchaseProducts_)
			{
				modInternalXMLHelperFunctions.AppendElements(parentNode_2, new string[4] { "isInventoried", "isSerialized", "isTaxable", "printBarcode" });
			}
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand(text + " Product query", xmlElement.OwnerDocument).DocumentElement.SelectNodes($"{text}ProductQuery/{text}Product"))
			{
				Product purchaseOrSellProductFromPurchaseProductElement = GetPurchaseOrSellProductFromPurchaseProductElement(item2, purchaseProducts_);
				if (purchaseProducts_)
				{
					list.Add((PurchaseProduct)purchaseOrSellProductFromPurchaseProductElement);
				}
				else
				{
					list2.Add((SellProduct)purchaseOrSellProductFromPurchaseProductElement);
				}
			}
		}
		if (purchaseProducts_)
		{
			return list;
		}
		return list2;
	}

	private Product GetPurchaseOrSellProductFromPurchaseProductElement(XmlElement productElement_, bool purchaseProduct_)
	{
		Product product = null;
		int productId_ = int.Parse(productElement_.GetAttribute("id"));
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(productElement_, "name");
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(productElement_, "productFamily");
		XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(productElement_, "productLine");
		XmlElement childElementIfThere3 = modInternalXMLHelperFunctions.GetChildElementIfThere(productElement_, "unitOfMeasure");
		int productLineId_ = int.Parse(childElementIfThere2.GetAttribute("id"));
		string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere2, "name");
		int productFamilyId_ = int.Parse(childElementIfThere.GetAttribute("id"));
		string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name");
		int unitOfMeasureId_ = int.Parse(childElementIfThere3.GetAttribute("id"));
		string textOfChildIfThere4 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere3, "name");
		int variantCount_ = int.Parse(productElement_.GetAttribute("variantCount"));
		bool booleanFromAttribute = GetBooleanFromAttribute(productElement_, "isInventoried");
		bool booleanFromAttribute2 = GetBooleanFromAttribute(productElement_, "isInactive");
		bool booleanFromAttribute3 = GetBooleanFromAttribute(productElement_, "isTaxable");
		bool booleanFromAttribute4 = GetBooleanFromAttribute(productElement_, "isSerialized");
		bool booleanFromAttribute5 = GetBooleanFromAttribute(productElement_, "printBarcode");
		product = ((!purchaseProduct_) ? ((Product)new SellProduct(productId_, textOfChildIfThere, productLineId_, textOfChildIfThere2, productFamilyId_, textOfChildIfThere3, booleanFromAttribute, booleanFromAttribute4, booleanFromAttribute3, booleanFromAttribute5, variantCount_, unitOfMeasureId_, textOfChildIfThere4, booleanFromAttribute2)) : ((Product)new PurchaseProduct(productId_, textOfChildIfThere, productLineId_, textOfChildIfThere2, productFamilyId_, textOfChildIfThere3, booleanFromAttribute, booleanFromAttribute4, booleanFromAttribute3, booleanFromAttribute5, variantCount_, unitOfMeasureId_, textOfChildIfThere4, booleanFromAttribute2)));
		foreach (XmlElement item in productElement_.SelectNodes("productAttributeType"))
		{
			int productAttributeTypeId_ = int.Parse(item.GetAttribute("id"));
			string textOfChildIfThere5 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "name");
			string textOfChildIfThere6 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "description");
			bool booleanFromAttribute6 = GetBooleanFromAttribute(item, "isCustomSort");
			product.ProductAttributeTypes.AddProductAttributeType(new ProductAttributeType(productAttributeTypeId_, textOfChildIfThere5, textOfChildIfThere6, booleanFromAttribute6));
		}
		product.ClearUpdateFlags();
		return product;
	}

	public List<ProductFamily> GetProductFamilies()
	{
		return GetProductFamilies(null);
	}

	public ProductFamily GetProductFamily(int productFamilyId_)
	{
		List<ProductFamily> productFamilies = GetProductFamilies(new int[1] { productFamilyId_ });
		if (productFamilies.Count == 0)
		{
			return null;
		}
		return productFamilies[0];
	}

	private List<ProductFamily> GetProductFamilies(IEnumerable<int> productFamilyIds_)
	{
		List<ProductFamily> list = new List<ProductFamily>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("productFamilyQuery");
		if (productFamilyIds_ != null)
		{
			flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in productFamilyIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "productFamily", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[1] { "name" });
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("ProductFamily query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("productFamilyQuery/productFamily"))
			{
				list.Add(GetProductFamilyFromProductFamilyElement(item2));
			}
		}
		return list;
	}

	private ProductFamily GetProductFamilyFromProductFamilyElement(XmlElement productFamilyElement_)
	{
		ProductFamily productFamily = new ProductFamily(int.Parse(productFamilyElement_.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(productFamilyElement_, "name"));
		productFamily.ClearUpdateFlags();
		return productFamily;
	}

	public List<ProductLine> GetProductLines()
	{
		return GetProductLines(null, null);
	}

	public List<ProductLine> GetProductLines(int productFamilyId_)
	{
		return GetProductLines(null, new int[1] { productFamilyId_ });
	}

	public ProductLine GetProductLine(int productLineId_)
	{
		List<ProductLine> productLines = GetProductLines(new int[1] { productLineId_ }, null);
		if (productLines.Count == 0)
		{
			return null;
		}
		return productLines[0];
	}

	private List<ProductLine> GetProductLines(IEnumerable<int> productLineIds_, IEnumerable<int> productFamilyIds_)
	{
		List<ProductLine> list = new List<ProductLine>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("productLineQuery");
		XmlElement xmlElement2 = null;
		if (productLineIds_ != null)
		{
			flag = true;
			xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in productLineIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "productLine", item);
			}
		}
		if (productFamilyIds_ != null)
		{
			flag = true;
			if (xmlElement2 == null)
			{
				xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			}
			foreach (int item2 in productFamilyIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "productFamily", item2);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
			modInternalXMLHelperFunctions.AppendElement(parentNode_, "name");
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_, "productFamily"), "name");
			foreach (XmlElement item3 in ExecuteAndIfNecessaryTraceCommand("ProductLine query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("productLineQuery/productLine"))
			{
				list.Add(GetProductLineFromProductLineElement(item3));
			}
		}
		return list;
	}

	private ProductLine GetProductLineFromProductLineElement(XmlElement productLineElement_)
	{
		int productLineId_ = int.Parse(productLineElement_.GetAttribute("id"));
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(productLineElement_, "name");
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(productLineElement_, "productFamily");
		int productFamilyId_ = int.Parse(childElementIfThere.GetAttribute("id"));
		string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name");
		ProductLine productLine = new ProductLine(productLineId_, textOfChildIfThere, productFamilyId_, textOfChildIfThere2);
		productLine.ClearUpdateFlags();
		return productLine;
	}

	public CostList GetCostList(int costListId_)
	{
		if (costListId_ == 0)
		{
			throw new Exception("Invalid argument.  costListId_ can not be '0'.");
		}
		List<CostList> costLists = GetCostLists(new int[1] { costListId_ });
		if (costLists.Count == 0)
		{
			return null;
		}
		return costLists[0];
	}

	public List<CostList> GetCostLists()
	{
		return GetCostLists(null);
	}

	private List<CostList> GetCostLists(IEnumerable<int> costListIds_)
	{
		List<CostList> list = null;
		list = new List<CostList>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("costListQuery");
		if (costListIds_ != null)
		{
			flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in costListIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "costList", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
			modInternalXMLHelperFunctions.AppendElement(parentNode_2, "name");
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_2, "supplier"), "name");
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("CostList query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("costListQuery/costList"))
			{
				list.Add(GetCostListFromCostListElement(item2));
			}
		}
		return list;
	}

	private CostList GetCostListFromCostListElement(XmlElement costListElement_)
	{
		CostList costList = new CostList(int.Parse(costListElement_.GetAttribute("id")));
		costList.CostListName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(costListElement_, "name");
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(costListElement_, "supplier");
		costList.SetSupplier(int.Parse(childElementIfThere.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name"));
		costList.ClearUpdateFlags();
		return costList;
	}

	public LabelTemplate GetLabelTemplate(int labelTemplateId_)
	{
		List<LabelTemplate> labelTemplates = GetLabelTemplates(new int[1] { labelTemplateId_ });
		if (labelTemplates.Count > 0)
		{
			return labelTemplates[0];
		}
		return null;
	}

	public List<LabelTemplate> GetLabelTemplates()
	{
		return GetLabelTemplates(null, getAll_: true);
	}

	public List<LabelTemplate> GetLabelTemplates(IEnumerable<int> labelTemplateIds_)
	{
		return GetLabelTemplates(labelTemplateIds_, getAll_: false);
	}

	private List<LabelTemplate> GetLabelTemplates(IEnumerable<int> labelTemplateIds_, bool getAll_)
	{
		List<LabelTemplate> list = null;
		ValidateConnected();
		list = new List<LabelTemplate>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("labelTemplateQuery");
		if (labelTemplateIds_ != null)
		{
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item2 in labelTemplateIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "labelTemplate", item2);
			}
		}
		if (flag && getAll_)
		{
			flag = false;
		}
		if (!flag)
		{
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[1] { "all" });
			foreach (XmlElement item3 in ExecuteAndIfNecessaryTraceCommand("Label Template query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("labelTemplateQuery/labelTemplate"))
			{
				string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "name");
				int id_ = int.Parse(item3.GetAttribute("id"));
				bool isInactive_ = "1" == item3.GetAttribute("isInactive");
				int seqNum_ = int.Parse(item3.GetAttribute("seqNum"));
				LabelTemplate item = new LabelTemplate(id_, textOfChildIfThere, isInactive_, seqNum_)
				{
					PageHeightInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "pageHeightInches")),
					PageWidthInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "pageWidthInches")),
					MarginBottomInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "marginBottomInches")),
					MarginTopInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "marginTopInches")),
					MarginRightInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "marginRightInches")),
					MarginLeftInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "marginLeftInches")),
					LabelHeightInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "labelHeightInches")),
					LabelWidthInches = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "labelWidthInches")),
					ColumnsPerPage = Convert.ToInt32(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "columnsPerPage")),
					RowsPerPage = Convert.ToInt32(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item3, "rowsPerPage")),
					DrawBorder = GetBooleanFromAttribute(item3, "drawBorder"),
					PrintRowsThenColumns = GetBooleanFromAttribute(item3, "printRowsThenColumns")
				};
				list.Add(item);
			}
		}
		return list;
	}

	public bool DownloadLabelForSerialNumber(int labelTemplateId_, FileInfo targetPath_, int serialNumberId_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false)
	{
		return DownloadLabelsForSerialNumbers(labelTemplateId_, targetPath_, new int[1] { serialNumberId_ }, overwriteExistingFile_, suppressExceptions_);
	}

	public bool DownloadLabelsForSerialNumbers(int labelTemplateId_, FileInfo targetPath_, IEnumerable<int> serialNumberIds_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false)
	{
		return DownloadLabelFile(labelTemplateId_, serialNumberIds_, null, null, targetPath_, overwriteExistingFile_, suppressExceptions_);
	}

	public bool DownloadLabelsForPurchaseOrder(int labelTemplateId_, FileInfo targetPath_, int purchaseOrderId_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false)
	{
		return DownloadLabelFile(labelTemplateId_, null, purchaseOrderId_, null, targetPath_, overwriteExistingFile_, suppressExceptions_);
	}

	public bool DownloadLabelsForPurchaseOrderReceipt(int labelTemplateId_, FileInfo targetPath_, int purchaseOrderReceiptId_, bool overwriteExistingFile_ = false, bool suppressExceptions_ = false)
	{
		return DownloadLabelFile(labelTemplateId_, null, null, purchaseOrderReceiptId_, targetPath_, overwriteExistingFile_, suppressExceptions_);
	}

	private bool DownloadLabelFile(int labelTemplateId_, IEnumerable<int> serialNumberIds_, int? poId_, int? poReceiptId_, FileInfo targetPath_, bool overwriteExistingFile_, bool suppressExceptions_)
	{
		bool result = false;
		if (suppressExceptions_)
		{
			try
			{
				UncaughtDownloadLabelFile(labelTemplateId_, serialNumberIds_, poId_, poReceiptId_, targetPath_, overwriteExistingFile_);
				result = true;
			}
			catch (Exception)
			{
			}
		}
		else
		{
			UncaughtDownloadLabelFile(labelTemplateId_, serialNumberIds_, poId_, poReceiptId_, targetPath_, overwriteExistingFile_);
			result = true;
		}
		return result;
	}

	private void UncaughtDownloadLabelFile(int labelTemplateId_, IEnumerable<int> serialNumberIds_, int? poId_, int? poReceiptId_, FileInfo targetPath_, bool overwriteExistingFile_)
	{
		ValidateConnected();
		if (targetPath_.Exists)
		{
			if (!overwriteExistingFile_)
			{
				throw new Exception("File exists!");
			}
			targetPath_.Delete();
		}
		FileInfo fileInfo = new FileInfo(Path.GetTempFileName());
		using (FileStream fileStream = fileInfo.OpenWrite())
		{
			XmlElement xmlElement = CreateCommandDocument("labelFileDownload");
			xmlElement.SetAttribute("labelTemplateId", $"{labelTemplateId_}");
			if (serialNumberIds_ != null)
			{
				foreach (int item in serialNumberIds_)
				{
					modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "serialNumber", item);
				}
			}
			if (poId_.HasValue)
			{
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "purchaseOrder", poId_.Value);
			}
			if (poReceiptId_.HasValue)
			{
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "purchaseOrderReceipt", poReceiptId_.Value);
			}
			XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("Label File download", xmlElement.OwnerDocument);
			if (int.Parse(modInternalXMLHelperFunctions.GetChildElementIfThere(xmlDocument.DocumentElement, "labelFileDownload/payloadDescription").GetAttribute("fileSize")) > 0)
			{
				byte[] array = Convert.FromBase64String(modInternalXMLHelperFunctions.GetTextOfChildIfThere(xmlDocument.DocumentElement, "labelFileDownload/payload/data"));
				if (array.Length != 0)
				{
					fileStream.Write(array, 0, array.Length);
				}
			}
		}
		if (fileInfo.Exists)
		{
			fileInfo.MoveTo(targetPath_.FullName);
		}
	}

	public List<ProductAttributeType> GetProductAttributeTypes()
	{
		List<ProductAttributeType> list = new List<ProductAttributeType>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("productAttributeTypeQuery");
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[3] { "name", "description", "isCustomSort" });
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Product Attribute Type query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("productAttributeTypeQuery/productAttributeType"))
		{
			_ = "1" == item.GetAttribute("isInactive");
			bool isCustomSort_ = "1" == item.GetAttribute("isCustomSort");
			list.Add(new ProductAttributeType(int.Parse(item.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "name"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "description"), isCustomSort_));
		}
		return list;
	}

	public List<ProductAttributeValue> GetProductAttributeValues(int productAttributeTypeId_)
	{
		ValidateConnected();
		List<ProductAttributeValue> list = new List<ProductAttributeValue>();
		XmlElement xmlElement = CreateCommandDocument("productAttributeValueQuery");
		modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "productAttributeType", productAttributeTypeId_);
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[5] { "value", "description", "seqNum", "productAttributeTypeName", "isInactive" });
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Product Attribute Values query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("productAttributeValueQuery/productAttributeType/productAttributeValue"))
		{
			int productAttributeValueId_ = int.Parse(item.GetAttribute("id"));
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "value");
			string description_ = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "description"));
			_ = (XmlElement)item.ParentNode;
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere((XmlElement)item.ParentNode, "productAttributeTypeName");
			int productAttributeTypeId_2 = int.Parse(((XmlElement)item.ParentNode).GetAttribute("id"));
			bool booleanFromAttribute = GetBooleanFromAttribute(item, "isInactive");
			int? seqNum_ = GetNullableIntFromAttribute(item, "seqNum");
			if (item.HasAttribute("seqNum"))
			{
				seqNum_ = int.Parse(item.GetAttribute("seqNum"));
			}
			list.Add(new ProductAttributeValue(productAttributeValueId_, textOfChildIfThere, description_, seqNum_, productAttributeTypeId_2, textOfChildIfThere2, booleanFromAttribute));
		}
		return list;
	}

	public UnitOfMeasure GetUnitOfMeasure(int unitOfMeasureId_)
	{
		List<UnitOfMeasure> unitOfMeasures = GetUnitOfMeasures(new int[1] { unitOfMeasureId_ });
		if (unitOfMeasures.Count == 0)
		{
			return null;
		}
		return unitOfMeasures[0];
	}

	public List<UnitOfMeasure> GetUnitOfMeasures()
	{
		return GetUnitOfMeasures(null);
	}

	private List<UnitOfMeasure> GetUnitOfMeasures(IEnumerable<int> unitOfMeasureIds_)
	{
		List<UnitOfMeasure> list = new List<UnitOfMeasure>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("unitOfMeasureQuery");
		if (unitOfMeasureIds_ != null)
		{
			flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in unitOfMeasureIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElement(parentNode_, "unitOfMeasure").SetAttribute("id", item.ToString());
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[6] { "name", "seqNum", "multiplier", "divisor", "measurementLabel", "measurementQty" });
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("UnitOfMeasure query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("unitOfMeasureQuery/unitOfMeasure"))
			{
				list.Add(GetUnitOfMeasureFromUnitOfMeasureElement(item2));
			}
		}
		return list;
	}

	private UnitOfMeasure GetUnitOfMeasureFromUnitOfMeasureElement(XmlElement unitOfMeasureElement_)
	{
		UnitOfMeasure unitOfMeasure = new UnitOfMeasure(int.Parse(unitOfMeasureElement_.GetAttribute("id")));
		unitOfMeasure.SetUnitOfMeasureName(modInternalXMLHelperFunctions.GetTextOfChildIfThere(unitOfMeasureElement_, "name"));
		unitOfMeasure.SetMeasurementLabel(modInternalXMLHelperFunctions.GetTextOfChildIfThere(unitOfMeasureElement_, "measurementLabel"));
		unitOfMeasure.SetMeasurementQuantity(int.Parse(unitOfMeasureElement_.GetAttribute("measurementQty")));
		unitOfMeasure.SetDivisor(decimal.Parse(unitOfMeasureElement_.GetAttribute("divisor")));
		unitOfMeasure.SetMultiplier(decimal.Parse(unitOfMeasureElement_.GetAttribute("multiplier")));
		unitOfMeasure.SetSeqNum(int.Parse(unitOfMeasureElement_.GetAttribute("seqNum")));
		unitOfMeasure.ClearUpdateFlags();
		return unitOfMeasure;
	}

	public List<PriceList> GetPriceLists()
	{
		List<PriceList> list = null;
		list = new List<PriceList>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("priceListQuery");
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[3] { "name", "isInactive", "defaultTaxPercent" });
		foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Price List query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("priceListQuery/priceList"))
		{
			bool isInactive_ = "1" == item2.GetAttribute("isInactive");
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "defaultTaxPercent");
			PriceList item = new PriceList(int.Parse(item2.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item2, "name"), ParseDecimalIfThere(textOfChildIfThere), isInactive_);
			list.Add(item);
		}
		return list;
	}

	public PurchaseProductVariant GetPurchaseProductVariant(int variantId_)
	{
		List<PurchaseProductVariant> purchaseProductVariants = GetPurchaseProductVariants(new PurchaseProductVariant[1]
		{
			new PurchaseProductVariant(variantId_, null, 0, null)
		});
		if (purchaseProductVariants.Count > 0)
		{
			return purchaseProductVariants[0];
		}
		return null;
	}

	public SellProductVariant GetSellProductVariant(int variantId_)
	{
		List<SellProductVariant> sellProductVariants = GetSellProductVariants(new SellProductVariant[1]
		{
			new SellProductVariant(variantId_, null, 0, null)
		});
		if (sellProductVariants.Count > 0)
		{
			return sellProductVariants[0];
		}
		return null;
	}

	public List<PurchaseProductVariant> GetPurchaseProductVariants(IEnumerable<PurchaseProductVariant> purchaseProductVariants_)
	{
		return (List<PurchaseProductVariant>)GetPurchaseOrSellProductVariants(purchaseProductVariants_, purchaseProducts_: true);
	}

	public List<SellProductVariant> GetSellProductVariants(IEnumerable<SellProductVariant> sellProductVariants_)
	{
		return (List<SellProductVariant>)GetPurchaseOrSellProductVariants(sellProductVariants_, purchaseProducts_: false);
	}

	public List<PurchaseProductVariant> GetPurchaseProductVariants(IEnumerable<int> purchaseProductVariantIds_)
	{
		return (List<PurchaseProductVariant>)GetPurchaseOrSellProductVariants(purchaseProductVariantIds_, null, purchaseProducts_: true);
	}

	public List<SellProductVariant> GetSellProductVariants(IEnumerable<int> sellProductVariantIds_)
	{
		return (List<SellProductVariant>)GetPurchaseOrSellProductVariants(sellProductVariantIds_, null, purchaseProducts_: false);
	}

	internal object GetPurchaseOrSellProductVariants<T>(IEnumerable<T> pvs_, bool purchaseProducts_) where T : ProductVariant
	{
		List<int> list = new List<int>();
		List<ProductVariant> list2 = new List<ProductVariant>();
		foreach (T item in pvs_)
		{
			if (item.ProductVariantId > 0)
			{
				list.Add(item.ProductVariantId);
				continue;
			}
			if (item.ProductId > 0)
			{
				list2.Add(item);
				continue;
			}
			throw new APIException("When looking up product variants, either the variant id must be set, or the product and a set of attribute values must be set.", APIException.APIErrorCodes_Enum.GeneralException);
		}
		return GetPurchaseOrSellProductVariants(list, list2, purchaseProducts_);
	}

	internal object GetPurchaseOrSellProductVariants(IEnumerable<int> variantIds_, List<ProductVariant> pvsForLookupByValue_, bool purchaseProducts_)
	{
		List<PurchaseProductVariant> list = null;
		List<SellProductVariant> list2 = null;
		object obj = null;
		string text = null;
		if (purchaseProducts_)
		{
			list = new List<PurchaseProductVariant>();
			obj = list;
			text = "purchase";
		}
		else
		{
			list2 = new List<SellProductVariant>();
			obj = list2;
			text = "sell";
		}
		bool flag = false;
		if (variantIds_ != null)
		{
			flag = variantIds_.GetEnumerator().MoveNext();
		}
		bool flag2 = false;
		if (pvsForLookupByValue_ != null)
		{
			flag2 = pvsForLookupByValue_.Count > 0;
		}
		if (flag || flag2)
		{
			XmlElement xmlElement = null;
			XmlElement xmlElement2 = null;
			if (flag)
			{
				xmlElement = CreateCommandDocument($"{text}ProductVariantQuery");
				xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
				foreach (int item in variantIds_)
				{
					modInternalXMLHelperFunctions.AppendElement(xmlElement2, $"{text}ProductVariant").SetAttribute("id", item.ToString());
				}
				AddIncludeElementsForProductVariantQuery(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), text);
			}
			if (flag2)
			{
				xmlElement = ((xmlElement != null) ? modInternalXMLHelperFunctions.AppendElement(xmlElement.ParentNode, $"{text}ProductVariantByValuesQuery") : CreateCommandDocument($"{text}ProductVariantByValuesQuery"));
				xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
				foreach (ProductVariant item2 in pvsForLookupByValue_)
				{
					XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement2, $"{text}ProductVariant");
					modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, $"{text}Product", item2.ProductId);
					foreach (ProductAttributeValue productAttributeValue in item2.ProductAttributeValues)
					{
						if (productAttributeValue.ProductAttributeValueId > 0)
						{
							modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "productAttributeValue", productAttributeValue.ProductAttributeValueId);
							continue;
						}
						XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "productAttributeValueValue");
						if (productAttributeValue.ProductAttributeTypeId > 0)
						{
							modInternalXMLHelperFunctions.AppendElementWithId(parentNode_2, "productAttributeType", productAttributeValue.ProductAttributeTypeId);
						}
						else
						{
							modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "productAttributeTypeName", productAttributeValue.ProductAttributeTypeName);
						}
						modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "value", productAttributeValue.Value);
					}
				}
				AddIncludeElementsForProductVariantQuery(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), text);
			}
			XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand($"{text}ProductVariant query", xmlElement.OwnerDocument);
			Dictionary<int, int> dictionary = new Dictionary<int, int>();
			foreach (XmlElement item3 in xmlDocument.DocumentElement.SelectNodes($"({text}ProductVariantQuery" + $"|{text}ProductVariantByValuesQuery)/{text}ProductVariant"))
			{
				ProductVariant productVariantFromPVElement = GetProductVariantFromPVElement(item3, purchaseProducts_);
				if (!dictionary.ContainsKey(productVariantFromPVElement.ProductVariantId))
				{
					if (purchaseProducts_)
					{
						list.Add((PurchaseProductVariant)productVariantFromPVElement);
					}
					else
					{
						list2.Add((SellProductVariant)productVariantFromPVElement);
					}
					dictionary.Add(productVariantFromPVElement.ProductVariantId, productVariantFromPVElement.ProductVariantId);
				}
			}
		}
		return obj;
	}

	private void AddIncludeElementsForProductVariantQuery(XmlElement includeElement_, string strPrefix_)
	{
		modInternalXMLHelperFunctions.AppendElement(includeElement_, "name");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(includeElement_, "productAttributeValue");
		modInternalXMLHelperFunctions.AppendElements(parentNode_, new string[4] { "value", "seqNum", "description", "isInactive" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(parentNode_, "productAttributeType"), "name");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(includeElement_, $"{strPrefix_}Product"), "name");
	}

	private ProductVariant GetProductVariantFromPVElement(XmlElement pvElement_, bool purchaseProducts_)
	{
		ProductVariant productVariant = null;
		string text = (purchaseProducts_ ? "purchase" : "sell").ToString();
		int value = GetNullableIntFromAttribute(pvElement_, "id", requireValue_: true).Value;
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(pvElement_, "name");
		int value2 = GetNullableIntFromAttribute(pvElement_, "id", requireValue_: true, $"{text}Product").Value;
		string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(pvElement_, text + "Product/name");
		productVariant = ((!purchaseProducts_) ? ((ProductVariant)new SellProductVariant(value, textOfChildIfThere, value2, textOfChildIfThere2)) : ((ProductVariant)new PurchaseProductVariant(value, textOfChildIfThere, value2, textOfChildIfThere2)));
		foreach (XmlElement item in pvElement_.SelectNodes("productAttributeValue"))
		{
			int value3 = GetNullableIntFromAttribute(item, "id", requireValue_: true).Value;
			string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "value");
			string textOfChildIfThere4 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "description");
			int? nullableIntFromAttribute = GetNullableIntFromAttribute(item, "seqNum");
			bool booleanFromAttribute = GetBooleanFromAttribute(item, "isInactive");
			XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(item, "productAttributeType");
			int value4 = GetNullableIntFromAttribute(childElementIfThere, "id", requireValue_: true).Value;
			string textOfChildIfThere5 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name");
			productVariant.ProductAttributeValues.AddProductAttributeValue(new ProductAttributeValue(value3, textOfChildIfThere3, textOfChildIfThere4, nullableIntFromAttribute, value4, textOfChildIfThere5, booleanFromAttribute));
		}
		productVariant.ClearUpdateFlags();
		return productVariant;
	}

	public ShipToLocation GetShipToLocation(int shipToLocationId_)
	{
		List<ShipToLocation> shipToLocations = GetShipToLocations(new int[1] { shipToLocationId_ });
		if (shipToLocations.Count == 0)
		{
			return null;
		}
		return shipToLocations[0];
	}

	public List<ShipToLocation> GetShipToLocations()
	{
		return GetShipToLocations(null);
	}

	private List<ShipToLocation> GetShipToLocations(IEnumerable<int> shipToLocationIds_)
	{
		List<ShipToLocation> list = null;
		list = new List<ShipToLocation>();
		bool flag = false;
		XmlElement xmlElement = CreateCommandDocument("shipToLocationQuery");
		if (shipToLocationIds_ != null)
		{
			flag = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in shipToLocationIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "shipToLocation", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
			modInternalXMLHelperFunctions.AppendElements(xmlElement2, new string[3] { "name", "seqNum", "isInactive" });
			AppendAddressInclude(xmlElement2);
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("ShipToLocation query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("shipToLocationQuery/shipToLocation"))
			{
				list.Add(GetShipToLocationFromShipToLocationElement(item2));
			}
		}
		return list;
	}

	private ShipToLocation GetShipToLocationFromShipToLocationElement(XmlElement shipToLocationElement_)
	{
		ShipToLocation shipToLocation = new ShipToLocation(int.Parse(shipToLocationElement_.GetAttribute("id")));
		shipToLocation.ShipToLocationName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(shipToLocationElement_, "name");
		shipToLocation.IsInactive = "1" == shipToLocationElement_.GetAttribute("isInactive");
		shipToLocation.Address = GetAddressFromAddressElement(modInternalXMLHelperFunctions.GetChildElementIfThere(shipToLocationElement_, "address"));
		shipToLocation.SetSeqNum(Convert.ToInt32(modInternalXMLHelperFunctions.GetTextOfChildIfThere(shipToLocationElement_, "seqNum")));
		shipToLocation.ClearUpdateFlags();
		return shipToLocation;
	}

	private List<PurchaseOrder> GetPurchaseOrders(IEnumerable<int> purchaseOrderIds_, IEnumerable<int> jobIds_, PurchaseOrderFilter purchaseOrderFilter_, PagingOptions pagingOptions_)
	{
		List<PurchaseOrder> list = null;
		list = new List<PurchaseOrder>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderQuery");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (purchaseOrderIds_ == null)
		{
			if (jobIds_ == null)
			{
				if (pagingOptions_ == null)
				{
					throw new Exception("Paging is required unless querying for a specific set of purchase orders by id.");
				}
				AppendViewFilterIfNecessary(xmlElement2, purchaseOrderFilter_.ViewId);
				AppendNecessaryCustomFilters(xmlElement2, purchaseOrderFilter_.CustomFieldFilters);
				AppendPOStatusFilterIfNecessary(xmlElement2, purchaseOrderFilter_.PurchaseOrderStatusFilters);
				AppendBuiltInDateFilters(xmlElement2, purchaseOrderFilter_.DateFilters);
				AppendBuiltInTextFilters(xmlElement2, purchaseOrderFilter_.TextFilters);
				AppendBuiltInListOfValuesFilters(xmlElement2, purchaseOrderFilter_.ListOfValuesFilters);
			}
			else
			{
				XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement2, "jobs");
				foreach (int item in jobIds_)
				{
					modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "job", item);
				}
			}
		}
		else
		{
			foreach (int item2 in purchaseOrderIds_)
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement2, "purchaseOrder").SetAttribute("id", item2.ToString());
			}
		}
		if (pagingOptions_ != null)
		{
			AppendPagingSpec(xmlElement, pagingOptions_.FirstRecord, pagingOptions_.PageSize);
		}
		ValidateConnected();
		XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElements(xmlElement3, new string[6] { "purchaseOrderNumber", "taxRate", "orderDate", "expectedDeliveryDate", "notes", "status" });
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "shipToLocation"), "name");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "costList"), "name");
		modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement3, "supplier"), "name");
		if (pagingOptions_ != null && pagingOptions_.TotalRecords.HasValue)
		{
			modInternalXMLHelperFunctions.AppendElement(xmlElement3, "totalRecords");
		}
		if (flag)
		{
			AddObjectCustomFieldIncludeElements(xmlElement3, "purchaseOrder");
		}
		XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("PurchaseOrder query", xmlElement.OwnerDocument);
		if (pagingOptions_ != null)
		{
			pagingOptions_.TotalRecords = GetNullableIntFromAttribute(modInternalXMLHelperFunctions.GetChildElementIfThere(xmlDocument.DocumentElement, "purchaseOrderQuery"), "totalRecords");
		}
		foreach (XmlElement item3 in xmlDocument.DocumentElement.SelectNodes("purchaseOrderQuery/purchaseOrder"))
		{
			list.Add(GetPurchaseOrderFromPurchaseOrderElement(item3));
		}
		return list;
	}

	public List<PurchaseOrder> GetPurchaseOrders(IEnumerable<int> purchaseOrderIds_)
	{
		bool flag = true;
		if (purchaseOrderIds_ != null && purchaseOrderIds_.GetEnumerator().MoveNext())
		{
			flag = false;
		}
		if (flag)
		{
			return new List<PurchaseOrder>();
		}
		return GetPurchaseOrders(purchaseOrderIds_, null, null, null);
	}

	public PurchaseOrder GetPurchaseOrder(int purchaseOrderId_)
	{
		List<PurchaseOrder> purchaseOrders = GetPurchaseOrders(new int[1] { purchaseOrderId_ });
		if (purchaseOrders.Count == 0)
		{
			return null;
		}
		return purchaseOrders[0];
	}

	public List<PurchaseOrder> GetPurchaseOrders(PurchaseOrderFilter purchaseOrderFilter_, PagingOptions pagingOptions_)
	{
		return GetPurchaseOrders(null, null, purchaseOrderFilter_, pagingOptions_);
	}

	public List<PurchaseOrder> GetPurchaseOrdersOfJobs(IEnumerable<int> jobIds_)
	{
		bool flag = true;
		if (jobIds_ != null && jobIds_.GetEnumerator().MoveNext())
		{
			flag = false;
		}
		if (flag)
		{
			return new List<PurchaseOrder>();
		}
		return GetPurchaseOrders(null, jobIds_, null, null);
	}

	public void AddJobsToPurchaseOrder(IEnumerable<int> jobIds_, int purchaseOrderId_)
	{
		CreateJobPOs(jobIds_, new int[1] { purchaseOrderId_ });
	}

	public void AddJobToPurchaseOrder(int jobId_, int purchaseOrderId_)
	{
		CreateJobPOs(new int[1] { jobId_ }, new int[1] { purchaseOrderId_ });
	}

	private PurchaseOrder GetPurchaseOrderFromPurchaseOrderElement(XmlElement purchaseOrderElement_)
	{
		PurchaseOrder purchaseOrder = new PurchaseOrder(int.Parse(purchaseOrderElement_.GetAttribute("id")));
		purchaseOrder.PurchaseOrderNumber = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderElement_, "purchaseOrderNumber");
		purchaseOrder.Notes = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderElement_, "notes"));
		purchaseOrder.TaxRate = ParseDecimalIfThere(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderElement_, "taxRate"));
		purchaseOrder.OrderDate = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderElement_, "orderDate"));
		purchaseOrder.ExpectedDeliveryDate = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderElement_, "expectedDeliveryDate"));
		purchaseOrder.SetStatus(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderElement_, "status"));
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(purchaseOrderElement_, "supplier");
		purchaseOrder.SetSupplier(int.Parse(childElementIfThere.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name"));
		XmlElement childElementIfThere2 = modInternalXMLHelperFunctions.GetChildElementIfThere(purchaseOrderElement_, "costList");
		purchaseOrder.SetCostList(int.Parse(childElementIfThere2.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere2, "name"));
		XmlElement childElementIfThere3 = modInternalXMLHelperFunctions.GetChildElementIfThere(purchaseOrderElement_, "shipToLocation");
		purchaseOrder.SetShipToLocation(int.Parse(childElementIfThere3.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere3, "name"));
		purchaseOrder.CustomFieldValues = GetCustomFieldValuesForObject(purchaseOrderElement_);
		purchaseOrder.ClearUpdateFlags();
		return purchaseOrder;
	}

	public void DeletePurchaseOrder(int purchaseOrderId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "purchaseOrder", purchaseOrderId_);
		ExecuteAndIfNecessaryTraceCommand("PurchaseOrder delete", xmlElement.OwnerDocument);
	}

	public void DeletePurchaseOrderLine(int purchaseOrderLineId_)
	{
		DeletePurchaseOrderLines(new int[1] { purchaseOrderLineId_ });
	}

	public void DeletePurchaseOrderLines(IEnumerable<int> purchaseOrderLineIds_)
	{
		DeleteByIds(purchaseOrderLineIds_, "purchaseOrderLine", "Purchase Order Line");
	}

	public int CreatePurchaseOrder(PurchaseOrder purchaseOrder_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "purchaseOrder");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "supplier", purchaseOrder_.SupplierId);
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "costList", purchaseOrder_.CostListId);
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "shipToLocation", purchaseOrder_.ShipToLocationId);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "purchaseOrderNumber", purchaseOrder_.PurchaseOrderNumber);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "notes", purchaseOrder_.Notes);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "taxRate", purchaseOrder_.TaxRate);
		if (purchaseOrder_.OrderDate.HasValue)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "orderDate", purchaseOrder_.OrderDate.Value.ToString("yyyy-MM-dd"));
		}
		if (purchaseOrder_.ExpectedDeliveryDate.HasValue)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "expectedDeliveryDate", purchaseOrder_.ExpectedDeliveryDate.Value.ToString("yyyy-MM-dd"));
		}
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, purchaseOrder_.CustomFieldValues, "purchaseOrder");
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("PurchaseOrder create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("purchaseOrderCreate/purchaseOrder");
		purchaseOrder_.PurchaseOrderId = int.Parse(xmlElement3.GetAttribute("id"));
		purchaseOrder_.ClearUpdateFlags();
		return purchaseOrder_.PurchaseOrderId;
	}

	public void UpdatePurchaseOrder(PurchaseOrder purchaseOrder_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "purchaseOrder", purchaseOrder_.PurchaseOrderId);
		if (purchaseOrder_.ModifiedShipToLocation)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "shipToLocation", purchaseOrder_.ShipToLocationId);
		}
		if (purchaseOrder_.ModifiedCostList)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "costList", purchaseOrder_.CostListId);
		}
		if (purchaseOrder_.ModifiedSupplier)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "supplier", purchaseOrder_.SupplierId);
		}
		if (purchaseOrder_.ModifiedPurchaseOrderNumber)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "purchaseOrderNumber", purchaseOrder_.PurchaseOrderNumber, includeEmptyTextElements_: true);
		}
		if (purchaseOrder_.ModifiedNotes)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "notes", purchaseOrder_.Notes, includeEmptyTextElements_: true);
		}
		if (purchaseOrder_.ModifiedTaxRate)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "taxRate", purchaseOrder_.TaxRate, includeEmptyTextElements_: true);
		}
		if (purchaseOrder_.ModifiedExpectedDeliveryDate)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "expectedDeliveryDate", purchaseOrder_.ExpectedDeliveryDate.HasValue ? purchaseOrder_.ExpectedDeliveryDate.Value.ToString("yyyy-MM-dd") : "", includeEmptyTextElements_: true);
		}
		if (purchaseOrder_.ModifiedOrderDate)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "orderDate", purchaseOrder_.OrderDate.HasValue ? purchaseOrder_.OrderDate.Value.ToString("yyyy-MM-dd") : "", includeEmptyTextElements_: true);
		}
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, purchaseOrder_.CustomFieldValues, "purchaseOrder");
		ExecuteAndIfNecessaryTraceCommand("purchaseOrder update", xmlElement.OwnerDocument);
		purchaseOrder_.ClearUpdateFlags();
	}

	public List<PurchaseOrderLine> GetPurchaseOrderLinesOfPurchaseOrders(IEnumerable<int> purchaseOrderIds_)
	{
		return GetPurchaseOrderLines(purchaseOrderIds_, null);
	}

	public PurchaseOrderLine GetPurchaseOrderLine(int purchaseOrderLineId_)
	{
		List<PurchaseOrderLine> purchaseOrderLines = GetPurchaseOrderLines(null, new int[1] { purchaseOrderLineId_ });
		if (purchaseOrderLines.Count > 0)
		{
			return purchaseOrderLines[0];
		}
		return null;
	}

	public List<PurchaseOrderLine> GetPurchaseOrderLines(int purchaseOrderId_)
	{
		return GetPurchaseOrderLines(new int[1] { purchaseOrderId_ }, null);
	}

	public List<PurchaseOrderLine> GetPurchaseOrderLines(IEnumerable<int> purchaseOrderLineIds_)
	{
		return GetPurchaseOrderLines(null, purchaseOrderLineIds_);
	}

	internal List<PurchaseOrderLine> GetPurchaseOrderLines(IEnumerable<int> poIds_, IEnumerable<int> poLineIds_)
	{
		List<PurchaseOrderLine> list = null;
		list = new List<PurchaseOrderLine>();
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderLineQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		bool flag = true;
		if (poIds_ != null)
		{
			foreach (int item in poIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseOrder", item);
			}
		}
		if (poLineIds_ != null)
		{
			foreach (int item2 in poLineIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseOrderLine", item2);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item3 in ExecuteAndIfNecessaryTraceCommand("PurchaseOrderLine query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("purchaseOrderLineQuery/*"))
			{
				list.Add(GetPurchaseOrderLineFromPurchaseOrderLineElement(item3));
			}
		}
		return list;
	}

	public int CreatePurchaseOrderProductLine(PurchaseOrderProductLine purchaseOrderProductLine_)
	{
		return CreatePurchaseOrderLine(purchaseOrderProductLine_);
	}

	public int CreatePurchaseOrderMiscellaneousLine(PurchaseOrderMiscellaneousLine purchaseOrderMiscellaneousLine_)
	{
		return CreatePurchaseOrderLine(purchaseOrderMiscellaneousLine_);
	}

	public void CreatePurchaseOrderLines(PurchaseOrderSplitLine purchaseOrderSplitLine_)
	{
		SplitPurchaseOrderLine(purchaseOrderSplitLine_);
	}

	public void CreatePurchaseOrderLines(IEnumerable<PurchaseOrderSplitLine> purchaseOrderSplitLines_)
	{
		SplitPurchaseOrderLines(purchaseOrderSplitLines_);
	}

	public void SplitPurchaseOrderLine(PurchaseOrderSplitLine purchaseOrderSplitLine_)
	{
		SplitPurchaseOrderLines(new PurchaseOrderSplitLine[1] { purchaseOrderSplitLine_ });
	}

	public void SplitPurchaseOrderLines(IEnumerable<PurchaseOrderSplitLine> purchaseOrderSplitLines_)
	{
		if (purchaseOrderSplitLines_ == null)
		{
			return;
		}
		ValidateConnected();
		List<PurchaseOrderSplitLine> list = new List<PurchaseOrderSplitLine>();
		int num = 0;
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderLineCreate");
		foreach (PurchaseOrderSplitLine item in purchaseOrderSplitLines_)
		{
			list.Add(item);
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "purchaseOrderSplitLine");
			modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseOrderLine", item.PurchaseOrderLineId);
			int num2 = 0;
			foreach (PurchaseOrderSplitLine.SplitMeasurement splitMeasurement in item.SplitMeasurements)
			{
				XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "splitLine");
				xmlElement2.SetAttribute("requestId", num + ":" + num2);
				foreach (Measurement measurement in splitMeasurement.Measurements)
				{
					modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "measurement", measurement.Value, includeEmptyTextElements_: true);
				}
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "availableQuantity", splitMeasurement.AvailableQuantity.ToString());
				if (splitMeasurement.UnreceivedSerialNumberIds != null)
				{
					foreach (int unreceivedSerialNumberId in splitMeasurement.UnreceivedSerialNumberIds)
					{
						modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "unreceivedSerialNumber", unreceivedSerialNumberId);
					}
				}
				if (splitMeasurement.PurchaseOrderReceiptIds != null)
				{
					foreach (int purchaseOrderReceiptId in splitMeasurement.PurchaseOrderReceiptIds)
					{
						modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "purchaseOrderReceipt", purchaseOrderReceiptId);
					}
				}
				num2++;
			}
			num++;
		}
		foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("PurchaseOrderLine create", xmlElement.OwnerDocument).DocumentElement.SelectNodes("purchaseOrderLineCreate/purchaseOrderSplitLine/splitLine"))
		{
			string[] array = item2.GetAttribute("requestId").Split(':');
			num = int.Parse(array[0]);
			int index = int.Parse(array[1]);
			list[num].SplitMeasurements[index].NewPurchaseOrderLineId = Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(item2, "purchaseOrderLine").GetAttribute("id"));
		}
	}

	private int CreatePurchaseOrderLine(PurchaseOrderMaterialLine purchaseOrderLine_)
	{
		if (purchaseOrderLine_.PurchaseOrderLineId != 0)
		{
			throw new Exception("When creating a purchase order line, you must use a new PO Line object.");
		}
		ValidateConnected();
		bool flag = purchaseOrderLine_.PurchaseOrderLineType == PurchaseOrderLine.PurchaseOrderLineType_Enum.Product;
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderLineCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, flag ? "purchaseOrderProductLine" : "purchaseOrderMiscellaneousLine");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "purchaseOrder", purchaseOrderLine_.PurchaseOrderId);
		if (purchaseOrderLine_.ModifiedIsTaxable)
		{
			xmlElement2.SetAttribute("isTaxable", purchaseOrderLine_.IsTaxable ? "1" : "0");
		}
		modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "orderedQty", purchaseOrderLine_.OrderedQuantity.ToString());
		if (purchaseOrderLine_.ModifiedUnitCost || !flag)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "unitCost", purchaseOrderLine_.UnitCost.ToString());
		}
		if (flag)
		{
			PurchaseOrderProductLine purchaseOrderProductLine = (PurchaseOrderProductLine)purchaseOrderLine_;
			if (purchaseOrderProductLine.PurchaseProductVariant == null)
			{
				throw new Exception("Missing PurchaseProductVariant creating a PurchaseOrderProductLine.");
			}
			foreach (Measurement measurement in purchaseOrderProductLine.Measurements)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "measurement", measurement.ToString());
			}
			if (purchaseOrderProductLine.PurchaseProductVariant.ProductVariantId > 0)
			{
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "purchaseProductVariant", purchaseOrderProductLine.PurchaseProductVariant.ProductVariantId);
			}
			else
			{
				XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement2, "purchaseProductVariantByValues");
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseProduct", purchaseOrderProductLine.PurchaseProductVariant.ProductId);
				foreach (ProductAttributeValue productAttributeValue in purchaseOrderProductLine.PurchaseProductVariant.ProductAttributeValues)
				{
					if (productAttributeValue.ProductAttributeValueId > 0)
					{
						modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "productAttributeValue", productAttributeValue.ProductAttributeValueId);
						continue;
					}
					XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "productAttributeValueValue");
					if (productAttributeValue.ProductAttributeTypeId > 0)
					{
						modInternalXMLHelperFunctions.AppendElementWithId(parentNode_2, "productAttributeType", productAttributeValue.ProductAttributeTypeId);
					}
					else
					{
						modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "productAttributeTypeName", productAttributeValue.ProductAttributeTypeName);
					}
					modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "value", productAttributeValue.Value);
				}
			}
		}
		else
		{
			PurchaseOrderMiscellaneousLine purchaseOrderMiscellaneousLine = (PurchaseOrderMiscellaneousLine)purchaseOrderLine_;
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "miscItemDescription", purchaseOrderMiscellaneousLine.MiscItemDescription);
		}
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("PurchaseOrderLine create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("purchaseOrderLineCreate/*");
		purchaseOrderLine_.PurchaseOrderLineId = int.Parse(xmlElement3.GetAttribute("id"));
		purchaseOrderLine_.ClearUpdateFlags();
		return purchaseOrderLine_.PurchaseOrderLineId;
	}

	public void UpdatePurchaseOrderProductLine(PurchaseOrderProductLine purchaseOrderProductLine_)
	{
		UpdatePurchaseOrderLine(purchaseOrderProductLine_);
	}

	public void UpdatePurchaseOrderMiscellaneousLine(PurchaseOrderMiscellaneousLine purchaseOrderMiscellaneousLine_)
	{
		UpdatePurchaseOrderLine(purchaseOrderMiscellaneousLine_);
	}

	private void UpdatePurchaseOrderLine(PurchaseOrderMaterialLine purchaseOrderLine_)
	{
		if (purchaseOrderLine_.PurchaseOrderLineId == 0)
		{
			throw new Exception("When updating a purchase order line, you must use an updated PO Line object.");
		}
		ValidateConnected();
		bool flag = purchaseOrderLine_.PurchaseOrderLineType == PurchaseOrderLine.PurchaseOrderLineType_Enum.Product;
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderLineUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, flag ? "purchaseOrderProductLine" : "purchaseOrderMiscellaneousLine", purchaseOrderLine_.PurchaseOrderLineId);
		if (purchaseOrderLine_.ModifiedIsTaxable)
		{
			xmlElement2.SetAttribute("isTaxable", purchaseOrderLine_.IsTaxable ? "1" : "0");
		}
		if (purchaseOrderLine_.ModifiedOrderedQuantity)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "orderedQty", purchaseOrderLine_.OrderedQuantity.ToString());
		}
		if (purchaseOrderLine_.ModifiedUnitCost)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "unitCost", purchaseOrderLine_.UnitCost.ToString());
		}
		if (flag)
		{
			PurchaseOrderProductLine purchaseOrderProductLine = (PurchaseOrderProductLine)purchaseOrderLine_;
			if (purchaseOrderProductLine.ModifiedMeasurements)
			{
				foreach (Measurement measurement in purchaseOrderProductLine.Measurements)
				{
					modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "measurement", measurement.ToString());
				}
			}
		}
		else
		{
			PurchaseOrderMiscellaneousLine purchaseOrderMiscellaneousLine = (PurchaseOrderMiscellaneousLine)purchaseOrderLine_;
			if (purchaseOrderMiscellaneousLine.ModifiedMiscItemDescription)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "miscItemDescription", purchaseOrderMiscellaneousLine.MiscItemDescription);
			}
		}
		ExecuteAndIfNecessaryTraceCommand("PurchaseOrderLine update", xmlElement.OwnerDocument);
		purchaseOrderLine_.ClearUpdateFlags();
	}

	public Supplier GetSupplier(int supplierId_)
	{
		List<Supplier> suppliers = GetSuppliers(new int[1] { supplierId_ });
		if (suppliers.Count == 0)
		{
			return null;
		}
		return suppliers[0];
	}

	public List<Supplier> GetSuppliers()
	{
		return GetSuppliers(null);
	}

	private List<Supplier> GetSuppliers(IEnumerable<int> supplierIds_)
	{
		List<Supplier> list = null;
		list = new List<Supplier>();
		bool flag = true;
		bool flag2 = false;
		XmlElement xmlElement = CreateCommandDocument("supplierQuery");
		if (supplierIds_ != null)
		{
			flag2 = true;
			XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
			foreach (int item in supplierIds_)
			{
				flag2 = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "supplier", item);
			}
		}
		if (!flag2)
		{
			ValidateConnected();
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
			modInternalXMLHelperFunctions.AppendElements(xmlElement2, new string[4] { "name", "taxRate", "notes", "isInactive" });
			AppendAddressInclude(xmlElement2);
			if (flag)
			{
				AddObjectCustomFieldIncludeElements(xmlElement2, "supplier");
			}
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Supplier query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("supplierQuery/supplier"))
			{
				list.Add(GetSupplierFromSupplierElement(item2));
			}
		}
		return list;
	}

	private Supplier GetSupplierFromSupplierElement(XmlElement supplierElement_)
	{
		Supplier supplier = new Supplier(int.Parse(supplierElement_.GetAttribute("id")));
		supplier.SupplierName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(supplierElement_, "name");
		supplier.Notes = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(supplierElement_, "notes"));
		supplier.TaxRate = ParseDecimalIfThere(modInternalXMLHelperFunctions.GetTextOfChildIfThere(supplierElement_, "taxRate"));
		supplier.Address = GetAddressFromAddressElement(modInternalXMLHelperFunctions.GetChildElementIfThere(supplierElement_, "address"));
		supplier.CustomFieldValues = GetCustomFieldValuesForObject(supplierElement_);
		supplier.IsInactive = GetBooleanFromAttribute(supplierElement_, "isInactive");
		supplier.ClearUpdateFlags();
		return supplier;
	}

	public void DeleteSupplier(int supplierId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("supplierDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "supplier", supplierId_);
		ExecuteAndIfNecessaryTraceCommand("Supplier delete", xmlElement.OwnerDocument);
	}

	public int CreateSupplier(Supplier supplier_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("supplierCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "supplier");
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", supplier_.SupplierName, includeEmptyTextElements_: true);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "notes", supplier_.Notes, includeEmptyTextElements_: true);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "taxRate", supplier_.TaxRate);
		if (supplier_.IsInactive)
		{
			xmlElement2.SetAttribute("isInactive", "1");
		}
		AppendAddressNodeIfNecessary(xmlElement2, supplier_.Address, "address", includeEmptyAddressFields_: true);
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, supplier_.CustomFieldValues, "supplier");
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Supplier create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("supplierCreate/supplier");
		supplier_.SetSupplierId(int.Parse(xmlElement3.GetAttribute("id")));
		supplier_.ClearUpdateFlags();
		return supplier_.SupplierId;
	}

	public void UpdateSupplier(Supplier supplier_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("supplierUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "supplier", supplier_.SupplierId);
		if (supplier_.ModifiedAddress)
		{
			AppendAddressNodeIfNecessary(xmlElement2, supplier_.Address, "address", includeEmptyAddressFields_: true);
		}
		if (supplier_.ModifiedSupplierName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", supplier_.SupplierName, includeEmptyTextElements_: true);
		}
		if (supplier_.ModifiedNotes)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "notes", supplier_.Notes, includeEmptyTextElements_: true);
		}
		if (supplier_.ModifiedTaxRate)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "taxRate", supplier_.TaxRate, includeEmptyTextElements_: true);
		}
		if (supplier_.ModifiedIsInactive)
		{
			xmlElement2.SetAttribute("isInactive", supplier_.IsInactive ? "1" : "0");
		}
		AddCustomFieldsUpdateOrCreationElement(xmlElement2, supplier_.CustomFieldValues, "supplier");
		ExecuteAndIfNecessaryTraceCommand("Supplier Update", xmlElement.OwnerDocument);
		supplier_.ClearUpdateFlags();
	}

	internal List<PurchaseOrderReceipt> InternalGetPurchaseOrderReceipts(IEnumerable<int> purchaseOrderReceiptIds_ = null, IEnumerable<int> purchaseOrderIds_ = null, IEnumerable<int> purchaseOrderLineIds_ = null)
	{
		List<PurchaseOrderReceipt> list = null;
		List<object> purchaseOrderReceiptsOrUnreceivedSerialNumbers = GetPurchaseOrderReceiptsOrUnreceivedSerialNumbers(purchaseOrderReceiptIds_, purchaseOrderIds_, purchaseOrderLineIds_, receipts_: true);
		list = new List<PurchaseOrderReceipt>();
		foreach (object item in purchaseOrderReceiptsOrUnreceivedSerialNumbers)
		{
			list.Add((PurchaseOrderReceipt)item);
		}
		return list;
	}

	internal List<UnreceivedSerialNumber> GetUnreceivedSerialNumbers(IEnumerable<int> unreceivedSerialNumberIds_, IEnumerable<int> purchaseOrderIds_, IEnumerable<int> purchaseOrderLineIds_)
	{
		List<UnreceivedSerialNumber> list = null;
		List<object> purchaseOrderReceiptsOrUnreceivedSerialNumbers = GetPurchaseOrderReceiptsOrUnreceivedSerialNumbers(unreceivedSerialNumberIds_, purchaseOrderIds_, purchaseOrderLineIds_, receipts_: false);
		list = new List<UnreceivedSerialNumber>();
		foreach (object item in purchaseOrderReceiptsOrUnreceivedSerialNumbers)
		{
			list.Add((UnreceivedSerialNumber)item);
		}
		return list;
	}

	internal List<object> GetPurchaseOrderReceiptsOrUnreceivedSerialNumbers(IEnumerable<int> porOrUSNIds_, IEnumerable<int> purchaseOrderIds_, IEnumerable<int> purchaseOrderLineIds_, bool receipts_)
	{
		List<object> list = null;
		list = new List<object>();
		bool flag = true;
		string text = (receipts_ ? "purchaseOrderReceipt" : "unreceivedSerialNumber");
		XmlElement xmlElement = CreateCommandDocument($"{text}Query");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (porOrUSNIds_ != null)
		{
			foreach (int item in porOrUSNIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElement(parentNode_, text).SetAttribute("id", item.ToString());
			}
		}
		if (purchaseOrderIds_ != null)
		{
			foreach (int item2 in purchaseOrderIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElement(parentNode_, "purchaseOrder").SetAttribute("id", item2.ToString());
			}
		}
		if (purchaseOrderLineIds_ != null)
		{
			foreach (int item3 in purchaseOrderLineIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElement(parentNode_, "purchaseOrderLine").SetAttribute("id", item3.ToString());
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item4 in ExecuteAndIfNecessaryTraceCommand($"{text} query", xmlElement.OwnerDocument).DocumentElement.SelectNodes($"{text}Query/{text}"))
			{
				list.Add(GetPurchaseOrderReceiptFromPurchaseOrderReceiptElement(item4, receipts_));
			}
		}
		return list;
	}

	private object GetPurchaseOrderReceiptFromPurchaseOrderReceiptElement(XmlElement purchaseOrderReceiptElement_, bool receipt_)
	{
		int num = int.Parse(purchaseOrderReceiptElement_.GetAttribute("id"));
		int value = GetNullableIntFromAttribute(purchaseOrderReceiptElement_, "id", requireValue_: true, "purchaseOrder").Value;
		int value2 = GetNullableIntFromAttribute(purchaseOrderReceiptElement_, "id", requireValue_: true, "purchaseOrderLine").Value;
		decimal quantity_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderReceiptElement_, "quantity"));
		DateTime deliveryDate_ = default(DateTime);
		if (receipt_)
		{
			deliveryDate_ = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderReceiptElement_, "deliveryDate")).Value;
		}
		SerialNumber serialNumber_ = null;
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(purchaseOrderReceiptElement_, "serialNumber");
		if (childElementIfThere != null)
		{
			serialNumber_ = GetSerialNumberFromSerialNumberElement(childElementIfThere);
		}
		JTObject jTObject = null;
		jTObject = ((!receipt_) ? ((JTObject)new UnreceivedSerialNumber(num, value, value2, quantity_, serialNumber_)) : ((JTObject)new PurchaseOrderReceipt(num, value, value2, quantity_, deliveryDate_, serialNumber_)));
		jTObject.ClearUpdateFlags();
		return jTObject;
	}

	public void DeletePurchaseOrderReceipt(int purchaseOrderReceiptId_, bool retainUnreceivedSerialNumbers_ = false)
	{
		DeletePurchaseOrderReceipts(new int[1] { purchaseOrderReceiptId_ }, retainUnreceivedSerialNumbers_);
	}

	public void DeletePurchaseOrderReceipts(IEnumerable<int> purchaseOrderReceiptIds_, bool retainUnreceivedSerialNumbers_ = false)
	{
		DeleteByIds(purchaseOrderReceiptIds_, "purchaseOrderReceipt", "Purchase Order Receipt", retainUnreceivedSerialNumbers_ ? "retainUnreceivedSerialNumbers" : null, retainUnreceivedSerialNumbers_ ? "1" : null);
	}

	public void DeleteUnreceivedSerialNumber(int unreceivedSerialNumberId_)
	{
		DeleteUnreceivedSerialNumbers(new int[1] { unreceivedSerialNumberId_ });
	}

	public void DeleteUnreceivedSerialNumbers(IEnumerable<int> unreceivedSerialNumberIds_)
	{
		DeleteByIds(unreceivedSerialNumberIds_, "unreceivedSerialNumber", "Unreceived Serial Number");
	}

	public List<PurchaseOrderReceipt> CreatePurchaseOrderReceiptsForPurchaseOrder(int purchaseOrderId_)
	{
		return CreatePurchaseOrderReceipts(new PurchaseOrderReceipt(purchaseOrderId_, PurchaseOrderReceipt.IdType_Enum.PurchaseOrder_IdType));
	}

	public List<PurchaseOrderReceipt> CreatePurchaseOrderReceiptsForPurchaseOrderLine(int purchaseOrderLineId_)
	{
		return CreatePurchaseOrderReceipts(new PurchaseOrderReceipt(purchaseOrderLineId_, PurchaseOrderReceipt.IdType_Enum.PurchaseOrderLine_IdType));
	}

	public List<PurchaseOrderReceipt> CreatePurchaseOrderReceiptsForPurchaseOrderLines(IEnumerable<int> purchaseOrderLineIds_)
	{
		return CreatePurchaseOrderReceipts(CreateListOfPORs(purchaseOrderLineIds_, PurchaseOrderReceipt.IdType_Enum.PurchaseOrderLine_IdType));
	}

	public List<PurchaseOrderReceipt> CreatePurchaseOrderReceiptsForUnreceivedSerialNumbers(IEnumerable<int> unreceivedSerialNumberIds_)
	{
		return CreatePurchaseOrderReceipts(CreateListOfPORs(unreceivedSerialNumberIds_, PurchaseOrderReceipt.IdType_Enum.UnreceivedSerialNumber_IdType));
	}

	private List<PurchaseOrderReceipt> CreateListOfPORs(IEnumerable<int> ids_, PurchaseOrderReceipt.IdType_Enum idType_)
	{
		List<PurchaseOrderReceipt> list = new List<PurchaseOrderReceipt>();
		foreach (int item in ids_)
		{
			list.Add(new PurchaseOrderReceipt(item, idType_));
		}
		return list;
	}

	public List<PurchaseOrderReceipt> CreatePurchaseOrderReceipts(PurchaseOrderReceipt purchaseOrderReceipt_)
	{
		return CreatePurchaseOrderReceipts(new PurchaseOrderReceipt[1] { purchaseOrderReceipt_ });
	}

	public List<PurchaseOrderReceipt> CreatePurchaseOrderReceipts(IEnumerable<PurchaseOrderReceipt> purchaseOrderReceipts_)
	{
		ValidateConnected();
		List<PurchaseOrderReceipt> list = new List<PurchaseOrderReceipt>();
		PurchaseOrderReceipt purchaseOrderReceipt = null;
		foreach (PurchaseOrderReceipt item in purchaseOrderReceipts_)
		{
			purchaseOrderReceipt = item;
			if (item.IdTypeUsedAtCreation == PurchaseOrderReceipt.IdType_Enum.PurchaseOrder_IdType || item.IdTypeUsedAtCreation == PurchaseOrderReceipt.IdType_Enum.PurchaseOrderLine_IdType || item.IdTypeUsedAtCreation == PurchaseOrderReceipt.IdType_Enum.UnreceivedSerialNumber_IdType)
			{
				list.Add(item);
			}
		}
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderReceiptCreate");
		int num = 0;
		for (num = 0; num < list.Count; num++)
		{
			purchaseOrderReceipt = list[num];
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "purchaseOrderReceipt");
			xmlElement2.SetAttribute("requestId", num.ToString());
			if (purchaseOrderReceipt.IdTypeUsedAtCreation == PurchaseOrderReceipt.IdType_Enum.UnreceivedSerialNumber_IdType)
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement2, "unreceivedSerialNumber").SetAttribute("id", purchaseOrderReceipt.UnreceivedSerialNumberId.ToString());
			}
			else if (purchaseOrderReceipt.IdTypeUsedAtCreation == PurchaseOrderReceipt.IdType_Enum.PurchaseOrderLine_IdType)
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement2, "purchaseOrderLine").SetAttribute("id", purchaseOrderReceipt.PurchaseOrderLineId.ToString());
			}
			else
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement2, "purchaseOrder").SetAttribute("id", purchaseOrderReceipt.PurchaseOrderId.ToString());
			}
			AddUpdateSerialNumberElementsIfNecessary(xmlElement2, purchaseOrderReceipt.SerialNumber);
			if (purchaseOrderReceipt.ModifiedQuantity)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", purchaseOrderReceipt.Quantity.ToString());
			}
			if (purchaseOrderReceipt.ModifiedDeliveryDate)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "deliveryDate", purchaseOrderReceipt.DeliveryDate.ToString("yyyy-MM-dd"));
			}
		}
		XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("Purchase Order Receipt create", xmlElement.OwnerDocument);
		Dictionary<int, PurchaseOrderReceipt> dictionary = new Dictionary<int, PurchaseOrderReceipt>();
		List<PurchaseOrderReceipt> list2 = new List<PurchaseOrderReceipt>();
		foreach (XmlElement item2 in xmlDocument.DocumentElement.SelectNodes("purchaseOrderReceiptCreate/purchaseOrderReceipt"))
		{
			Console.WriteLine("Got a PORelement.");
			int num2 = int.Parse(item2.GetAttribute("id"));
			int num3 = int.Parse(item2.GetAttribute("requestId"));
			purchaseOrderReceipt = list[num3];
			int? nullableIntFromAttribute = GetNullableIntFromAttribute(item2, "id", requireValue_: false, "serialNumber");
			if (purchaseOrderReceipt.IdTypeUsedAtCreation == PurchaseOrderReceipt.IdType_Enum.UnreceivedSerialNumber_IdType || (purchaseOrderReceipt.IdTypeUsedAtCreation == PurchaseOrderReceipt.IdType_Enum.PurchaseOrderLine_IdType && purchaseOrderReceipt.SerialNumber != null))
			{
				purchaseOrderReceipt.PurchaseOrderReceiptId = num2;
				if (nullableIntFromAttribute.HasValue)
				{
					if (purchaseOrderReceipt.SerialNumber == null)
					{
						purchaseOrderReceipt.SerialNumber = new SerialNumber(nullableIntFromAttribute.Value);
					}
					else
					{
						purchaseOrderReceipt.SerialNumber.SerialNumberId = nullableIntFromAttribute.Value;
					}
				}
			}
			else
			{
				purchaseOrderReceipt = ((!nullableIntFromAttribute.HasValue) ? new PurchaseOrderReceipt(num2, purchaseOrderReceipt.PurchaseOrderId, purchaseOrderReceipt.PurchaseOrderLineId, 0m, purchaseOrderReceipt.DeliveryDate, null) : new PurchaseOrderReceipt(num2, purchaseOrderReceipt.PurchaseOrderId, purchaseOrderReceipt.PurchaseOrderLineId, 0m, purchaseOrderReceipt.DeliveryDate, new SerialNumber(nullableIntFromAttribute.Value)));
				if (dictionary.ContainsKey(num3))
				{
					dictionary.Remove(num3);
				}
				dictionary.Add(num3, purchaseOrderReceipt);
			}
			list2.Add(purchaseOrderReceipt);
			purchaseOrderReceipt.ClearUpdateFlags();
		}
		foreach (int key in dictionary.Keys)
		{
			num = key;
			purchaseOrderReceipt = list[key];
			PurchaseOrderReceipt purchaseOrderReceipt2 = dictionary[key];
			purchaseOrderReceipt.PurchaseOrderReceiptId = purchaseOrderReceipt2.PurchaseOrderReceiptId;
			purchaseOrderReceipt.SerialNumber = purchaseOrderReceipt2.SerialNumber;
		}
		return list2;
	}

	public void UpdatePurchaseOrderReceipt(PurchaseOrderReceipt purchaseOrderReceipt_)
	{
		UpdatePurchaseOrderReceipts(new PurchaseOrderReceipt[1] { purchaseOrderReceipt_ });
	}

	public void UpdatePurchaseOrderReceipts(IEnumerable<PurchaseOrderReceipt> purchaseOrderReceipts_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("purchaseOrderReceiptUpdate");
		foreach (PurchaseOrderReceipt item in purchaseOrderReceipts_)
		{
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "purchaseOrderReceipt");
			xmlElement2.SetAttribute("id", $"{item.PurchaseOrderReceiptId}");
			if (item.ModifiedSerialNumber)
			{
				AddUpdateSerialNumberElementsIfNecessary(xmlElement2, item.SerialNumber);
			}
			if (item.ModifiedQuantity)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", item.Quantity.ToString());
			}
			if (item.ModifiedDeliveryDate)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "deliveryDate", item.DeliveryDate.ToString("yyyy-MM-dd"));
			}
		}
		ExecuteAndIfNecessaryTraceCommand("Purchase Order Receipt update", xmlElement.OwnerDocument);
	}

	private XmlElement AddUpdateSerialNumberElementsIfNecessary(XmlElement serialNumberElementParent_, SerialNumber serialNumber_)
	{
		XmlElement xmlElement = null;
		if (serialNumber_ != null)
		{
			xmlElement = modInternalXMLHelperFunctions.AppendElement(serialNumberElementParent_, "serialNumber");
			if (serialNumber_.ModifiedDescription)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "description", serialNumber_.Description, includeEmptyTextElements_: true);
			}
			if (serialNumber_.ModifiedBatchNumber)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "batchNumber", serialNumber_.BatchNumber, includeEmptyTextElements_: true);
			}
			if (serialNumber_.ModifiedSerialNumberName)
			{
				modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement, "name", serialNumber_.SerialNumberName, includeEmptyTextElements_: true);
			}
			if (serialNumber_.ModifiedInventoryLocation)
			{
				XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "inventoryLocation");
				if (serialNumber_.InventoryLocationId.HasValue)
				{
					xmlElement2.SetAttribute("id", serialNumber_.InventoryLocationId.ToString());
				}
			}
			AddCustomFieldsUpdateOrCreationElement(xmlElement, serialNumber_.CustomFieldValues, "serialNumber");
		}
		return xmlElement;
	}

	public List<UnreceivedSerialNumber> CreateUnreceivedSerialNumbers(int purchaseOrderProductLineId_)
	{
		return CreateUnreceivedSerialNumbers(new UnreceivedSerialNumber[1]
		{
			new UnreceivedSerialNumber(purchaseOrderProductLineId_)
		});
	}

	public List<UnreceivedSerialNumber> CreateUnreceivedSerialNumbers(UnreceivedSerialNumber unreceivedSerialNumber_)
	{
		return CreateUnreceivedSerialNumbers(new UnreceivedSerialNumber[1] { unreceivedSerialNumber_ });
	}

	public List<UnreceivedSerialNumber> CreateUnreceivedSerialNumbers(IEnumerable<UnreceivedSerialNumber> unreceivedSerialNumbers_)
	{
		ValidateConnected();
		List<UnreceivedSerialNumber> list = new List<UnreceivedSerialNumber>();
		UnreceivedSerialNumber unreceivedSerialNumber = null;
		foreach (UnreceivedSerialNumber item in unreceivedSerialNumbers_)
		{
			unreceivedSerialNumber = item;
			list.Add(item);
		}
		XmlElement xmlElement = CreateCommandDocument("unreceivedSerialNumberCreate");
		int num = 0;
		for (num = 0; num < list.Count; num++)
		{
			unreceivedSerialNumber = list[num];
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "unreceivedSerialNumber", num, "requestId");
			modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "purchaseOrderLine", unreceivedSerialNumber.PurchaseOrderLineId);
			AddUpdateSerialNumberElementsIfNecessary(xmlElement2, unreceivedSerialNumber.SerialNumber);
			if (unreceivedSerialNumber.ModifiedQuantity)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", unreceivedSerialNumber.Quantity.ToString());
			}
		}
		XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("Unreceived Serial Number create", xmlElement.OwnerDocument);
		Dictionary<int, UnreceivedSerialNumber> dictionary = new Dictionary<int, UnreceivedSerialNumber>();
		List<UnreceivedSerialNumber> list2 = new List<UnreceivedSerialNumber>();
		foreach (XmlElement item2 in xmlDocument.DocumentElement.SelectNodes("unreceivedSerialNumberCreate/unreceivedSerialNumber"))
		{
			int num2 = int.Parse(item2.GetAttribute("id"));
			int num3 = int.Parse(item2.GetAttribute("requestId"));
			unreceivedSerialNumber = list[num3];
			int value = GetNullableIntFromAttribute(item2, "id", requireValue_: true, "serialNumber").Value;
			if (unreceivedSerialNumber.SerialNumber == null)
			{
				unreceivedSerialNumber = new UnreceivedSerialNumber(num2, unreceivedSerialNumber.PurchaseOrderId, unreceivedSerialNumber.PurchaseOrderLineId, 0m, new SerialNumber(value));
				if (dictionary.ContainsKey(num3))
				{
					dictionary.Remove(num3);
				}
				dictionary.Add(num3, unreceivedSerialNumber);
			}
			else
			{
				unreceivedSerialNumber.SetUnreceivedSerialNumberId(num2);
				unreceivedSerialNumber.SerialNumber.SerialNumberId = value;
			}
			list2.Add(unreceivedSerialNumber);
			unreceivedSerialNumber.ClearUpdateFlags();
		}
		foreach (int key in dictionary.Keys)
		{
			num = key;
			unreceivedSerialNumber = list[key];
			UnreceivedSerialNumber unreceivedSerialNumber2 = dictionary[key];
			unreceivedSerialNumber.SetUnreceivedSerialNumberId(unreceivedSerialNumber2.UnreceivedSerialNumberId);
			unreceivedSerialNumber.SetSerialNumber(unreceivedSerialNumber2.SerialNumber);
		}
		return list2;
	}

	public void UpdateUnreceivedSerialNumber(UnreceivedSerialNumber unreceivedSerialNumber_)
	{
		UpdateUnreceivedSerialNumbers(new UnreceivedSerialNumber[1] { unreceivedSerialNumber_ });
	}

	public void UpdateUnreceivedSerialNumbers(IEnumerable<UnreceivedSerialNumber> unreceivedSerialNumbers_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("unreceivedSerialNumberUpdate");
		foreach (UnreceivedSerialNumber item in unreceivedSerialNumbers_)
		{
			XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "unreceivedSerialNumber", item.UnreceivedSerialNumberId);
			if (item.ModifiedSerialNumber)
			{
				AddUpdateSerialNumberElementsIfNecessary(xmlElement2, item.SerialNumber);
			}
			if (item.ModifiedQuantity)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", item.Quantity.ToString());
			}
		}
		ExecuteAndIfNecessaryTraceCommand("Unreceived Serial Number update", xmlElement.OwnerDocument);
	}

	public List<PurchaseOrderReceipt> GetPurchaseOrderReceipts(IEnumerable<int> purchaseOrderReceiptIds_)
	{
		return InternalGetPurchaseOrderReceipts(purchaseOrderReceiptIds_);
	}

	public PurchaseOrderReceipt GetPurchaseOrderReceipt(int purchaseOrderReceiptId_)
	{
		List<PurchaseOrderReceipt> list = InternalGetPurchaseOrderReceipts(new int[1] { purchaseOrderReceiptId_ });
		if (list.Count > 0)
		{
			return list[0];
		}
		return null;
	}

	public List<PurchaseOrderReceipt> GetPurchaseOrderReceiptsOfPurchaseOrders(IEnumerable<int> purchaseOrderIds_)
	{
		return InternalGetPurchaseOrderReceipts(null, purchaseOrderIds_);
	}

	public List<PurchaseOrderReceipt> GetPurchaseOrderReceiptsOfPurchaseOrder(int purchaseOrderId_)
	{
		return InternalGetPurchaseOrderReceipts(null, new int[1] { purchaseOrderId_ });
	}

	public List<PurchaseOrderReceipt> GetPurchaseOrderReceiptsOfPurchaseOrderLines(IEnumerable<int> purchaseOrderLineIds_)
	{
		return InternalGetPurchaseOrderReceipts(null, null, purchaseOrderLineIds_);
	}

	public List<PurchaseOrderReceipt> GetPurchaseOrderReceiptsOfPurchaseOrderLine(int purchaseOrderLineId_)
	{
		return InternalGetPurchaseOrderReceipts(null, null, new int[1] { purchaseOrderLineId_ });
	}

	private PurchaseOrderLine GetPurchaseOrderLineFromPurchaseOrderLineElement(XmlElement purchaseOrderLineElement_)
	{
		int value = GetNullableIntFromAttribute(purchaseOrderLineElement_, "id", requireValue_: true).Value;
		int value2 = GetNullableIntFromAttribute(purchaseOrderLineElement_, "id", requireValue_: true, "purchaseOrder").Value;
		int? nullableIntFromAttribute = GetNullableIntFromAttribute(purchaseOrderLineElement_, "id", requireValue_: false, "purchaseProductVariant");
		PurchaseProductVariant purchaseProductVariant = null;
		if (nullableIntFromAttribute.HasValue)
		{
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "purchaseProductVariant/name");
			int value3 = GetNullableIntFromAttribute(purchaseOrderLineElement_, "id", requireValue_: true, "purchaseProductVariant/purchaseProduct").Value;
			string textOfChildIfThere2 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "purchaseProductVariant/purchaseProduct/name");
			purchaseProductVariant = new PurchaseProductVariant(nullableIntFromAttribute.Value, textOfChildIfThere, value3, textOfChildIfThere2);
			foreach (XmlElement item in purchaseOrderLineElement_.SelectNodes("purchaseProductVariant/productAttributeValue"))
			{
				XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(item, "productAttributeType");
				ProductAttributeValue productAttributeValue_ = new ProductAttributeValue(int.Parse(item.GetAttribute("id")), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "value"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(item, "description"), GetNullableIntFromAttribute(item, "seqNum"), GetNullableIntFromAttribute(childElementIfThere, "id", requireValue_: true).Value, modInternalXMLHelperFunctions.GetTextOfChildIfThere(childElementIfThere, "name"), GetBooleanFromAttribute(item, "isInactive"));
				purchaseProductVariant.ProductAttributeValues.AddProductAttributeValue(productAttributeValue_);
			}
		}
		PurchaseOrderProductLine purchaseOrderProductLine = null;
		PurchaseOrderMaterialLine purchaseOrderMaterialLine = null;
		PurchaseOrderLine purchaseOrderLine = null;
		if (purchaseProductVariant == null)
		{
			PurchaseOrderMiscellaneousLine obj = new PurchaseOrderMiscellaneousLine(value2, value)
			{
				MiscItemDescription = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "miscItemDescription")
			};
			purchaseOrderLine = obj;
			purchaseOrderMaterialLine = obj;
		}
		else
		{
			purchaseOrderProductLine = new PurchaseOrderProductLine(value2, value, purchaseProductVariant)
			{
				MeasurementDescription = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "measurementDescription"),
				SerializableQuantity = decimal.Parse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "serializableQty")),
				IsSerializable = GetBooleanFromAttribute(purchaseOrderLineElement_, "isSerializable"),
				IsInventoried = GetBooleanFromAttribute(purchaseOrderLineElement_, "isInventoried")
			};
			foreach (XmlElement item2 in purchaseOrderLineElement_.SelectNodes("measurement"))
			{
				purchaseOrderProductLine.Measurements.AddMeasurement(new Measurement(decimal.Parse(item2.InnerText)));
			}
			purchaseOrderLine = purchaseOrderProductLine;
			purchaseOrderMaterialLine = purchaseOrderProductLine;
		}
		purchaseOrderLine.LineDescription = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "lineDescription");
		purchaseOrderMaterialLine.StatusName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "status");
		purchaseOrderMaterialLine.ReceivedQuantity = decimal.Parse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "receivedQty"));
		purchaseOrderMaterialLine.TotalUnitsDescription = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "totalUnitsDescription");
		purchaseOrderMaterialLine.TotalUnits = decimal.Parse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "totalUnits"));
		purchaseOrderMaterialLine.TotalCost = decimal.Parse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "totalCost"));
		purchaseOrderMaterialLine.UnitName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "unitName");
		purchaseOrderMaterialLine.UnitCost = decimal.Parse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "unitCost"));
		purchaseOrderMaterialLine.OrderedQuantity = decimal.Parse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "orderedQty"));
		purchaseOrderMaterialLine.IsTaxable = GetBooleanFromAttribute(purchaseOrderLineElement_, "isTaxable");
		string textOfChildIfThere3 = modInternalXMLHelperFunctions.GetTextOfChildIfThere(purchaseOrderLineElement_, "deliveryDate");
		purchaseOrderMaterialLine.DeliveryDate = ParseDate(textOfChildIfThere3);
		purchaseOrderLine.ClearUpdateFlags();
		return purchaseOrderLine;
	}

	public void DeleteQuote(int quoteId_)
	{
		XmlElement xmlElement = CreateCommandDocument("quoteDelete");
		ValidateConnected();
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "quote", quoteId_);
		ExecuteAndIfNecessaryTraceCommand("Quote delete", xmlElement.OwnerDocument);
	}

	public List<Salesperson> GetSalespeople()
	{
		return GetSalespersonOrSalespeople(null);
	}

	private List<Salesperson> GetSalespersonOrSalespeople(int? salesPersonId_)
	{
		List<Salesperson> list = new List<Salesperson>();
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("salespersonQuery");
		if (salesPersonId_.HasValue)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter"), "salesperson", salesPersonId_.Value);
		}
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[3] { "name", "isInactive", "accountingId" });
		foreach (XmlElement item in ExecuteAndIfNecessaryTraceCommand("Salesperson query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("salespersonQuery/salesperson"))
		{
			list.Add(GetSalespersonFromSalespersonElement(item));
		}
		return list;
	}

	public Salesperson GetSalesperson(int salesPersonId_)
	{
		List<Salesperson> salespersonOrSalespeople = GetSalespersonOrSalespeople(salesPersonId_);
		if (salespersonOrSalespeople.Count == 0)
		{
			return null;
		}
		return salespersonOrSalespeople[0];
	}

	public void DeleteSalesperson(int salespersonId_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("salespersonDelete");
		modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "salesperson", salespersonId_);
		ExecuteAndIfNecessaryTraceCommand("Salesperson delete", xmlElement.OwnerDocument);
	}

	private Salesperson GetSalespersonFromSalespersonElement(XmlElement salesPersonElement_)
	{
		if (salesPersonElement_ == null)
		{
			return null;
		}
		bool isInactive = "1" == salesPersonElement_.GetAttribute("isInactive");
		return new Salesperson(int.Parse(salesPersonElement_.GetAttribute("id")))
		{
			SalespersonName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(salesPersonElement_, "name"),
			AccountingId = modInternalXMLHelperFunctions.GetTextOfChildIfThere(salesPersonElement_, "accountingId"),
			IsInactive = isInactive
		};
	}

	public int CreateSalesperson(Salesperson salesperson_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("salespersonCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "salesperson");
		if (salesperson_.IsInactive)
		{
			xmlElement2.SetAttribute("isInactive", "1");
		}
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", salesperson_.SalespersonName, includeEmptyTextElements_: true);
		modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "accountingId", salesperson_.AccountingId, includeEmptyTextElements_: true);
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Salesperson create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("salespersonCreate/salesperson");
		salesperson_.SetSalespersonId(int.Parse(xmlElement3.GetAttribute("id")));
		salesperson_.ClearUpdateFlags();
		return salesperson_.SalespersonId;
	}

	public void UpdateSalesperson(Salesperson salesperson_)
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("salespersonUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "salesperson", salesperson_.SalespersonId);
		if (salesperson_.ModifiedIsInactive)
		{
			xmlElement2.SetAttribute("isInactive", $"{(salesperson_.IsInactive ? 1 : 0)}");
		}
		if (salesperson_.ModifiedSalespersonName)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "name", salesperson_.SalespersonName, includeEmptyTextElements_: true);
		}
		if (salesperson_.ModifiedAccountingId)
		{
			modInternalXMLHelperFunctions.AppendObjectAsTextElement(xmlElement2, "accountingId", salesperson_.AccountingId, includeEmptyTextElements_: true);
		}
		ExecuteAndIfNecessaryTraceCommand("Salesperson update", xmlElement.OwnerDocument);
		salesperson_.ClearUpdateFlags();
	}

	public SerialNumberImport GetSerialNumberImport(int serialNumberImportId_)
	{
		List<SerialNumberImport> serialNumberImports = GetSerialNumberImports(new int[1] { serialNumberImportId_ });
		if (serialNumberImports.Count > 0)
		{
			return serialNumberImports[0];
		}
		return null;
	}

	public List<SerialNumberImport> GetSerialNumberImports(IEnumerable<int> serialNumberImportIds_)
	{
		List<SerialNumberImport> list = null;
		ValidateConnected();
		list = new List<SerialNumberImport>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("serialNumberImportQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (serialNumberImportIds_ != null)
		{
			foreach (int item in serialNumberImportIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElement(parentNode_, "serialNumberImport").SetAttribute("id", item.ToString());
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Serial number import query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("serialNumberImportQuery/serialNumberImport"))
			{
				list.Add(GetImportFromImportElement(item2));
			}
		}
		return list;
	}

	private SerialNumberImport GetImportFromImportElement(XmlElement importElement_)
	{
		int serialNumberImportId_ = int.Parse(importElement_.GetAttribute("id"));
		decimal unitCost_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(importElement_, "unitCost"));
		decimal quantity_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(importElement_, "quantity"));
		DateTime value = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(importElement_, "creationDate")).Value;
		bool booleanFromAttribute = GetBooleanFromAttribute(importElement_, "isRemnant");
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(importElement_, "serialNumber");
		SerialNumber serialNumberFromSerialNumberElement = GetSerialNumberFromSerialNumberElement(childElementIfThere);
		SerialNumberImport serialNumberImport = new SerialNumberImport(serialNumberImportId_, 0, unitCost_, value, serialNumberFromSerialNumberElement, quantity_, booleanFromAttribute);
		foreach (XmlElement item in importElement_.SelectNodes("measurement"))
		{
			serialNumberImport.Measurements.AddMeasurement(new Measurement(decimal.Parse(item.InnerText)));
		}
		serialNumberImport.ClearUpdateFlags();
		return serialNumberImport;
	}

	private void AppendPPVCommandElements(XmlElement ppvParentElement_, int ppvId_, int productId_, ProductAttributeValueContainer attrs_, bool usePPVId_)
	{
		if (usePPVId_)
		{
			modInternalXMLHelperFunctions.AppendElementWithId(ppvParentElement_, "purchaseProductVariant", ppvId_);
			return;
		}
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(ppvParentElement_, "purchaseProductVariantByValues");
		modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseProduct", productId_);
		foreach (ProductAttributeValue item in attrs_)
		{
			if (item.ProductAttributeValueId > 0)
			{
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "productAttributeValue", item.ProductAttributeValueId);
				continue;
			}
			XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "productAttributeValueValue");
			if (item.ProductAttributeTypeId > 0)
			{
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_2, "productAttributeType", item.ProductAttributeTypeId);
			}
			else
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "productAttributeTypeName", item.ProductAttributeTypeName);
			}
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "value", item.Value);
		}
	}

	public int CreateSerialNumberImport(SerialNumberImport serialNumberImport_)
	{
		if (serialNumberImport_.SerialNumberImportId != 0)
		{
			throw new Exception("When creating a serial number import, you must use a new SerialNumberImport object");
		}
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("serialNumberImportCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "serialNumberImport");
		AppendPPVCommandElements(xmlElement2, serialNumberImport_.PurchaseProductVariantId, serialNumberImport_.PurchaseProductId, serialNumberImport_.ProductAttributeValues, serialNumberImport_.PrepedToCreateByPVId);
		if (serialNumberImport_.ModifiedCreationDate)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "creationDate", serialNumberImport_.CreationDate.ToString("yyyy-MM-dd"));
		}
		if (serialNumberImport_.ModifiedQuantity)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", serialNumberImport_.Quantity.ToString());
		}
		if (serialNumberImport_.ModifiedMeasurements)
		{
			foreach (Measurement measurement in serialNumberImport_.Measurements)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "measurement", measurement.ToString());
			}
		}
		if (serialNumberImport_.ModifiedUnitCost)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "unitCost", serialNumberImport_.UnitCost.ToString());
		}
		AddUpdateSerialNumberElementsIfNecessary(xmlElement2, serialNumberImport_.SerialNumber);
		if (serialNumberImport_.ModifiedIsRemnant)
		{
			xmlElement2.SetAttribute("isRemnant", serialNumberImport_.IsRemnant ? "1" : "0");
		}
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Serial number import create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("serialNumberImportCreate/*");
		serialNumberImport_.SerialNumberImportId = int.Parse(xmlElement3.GetAttribute("id"));
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(xmlElement3, "serialNumber");
		if (serialNumberImport_.SerialNumber == null)
		{
			serialNumberImport_.SerialNumber = new SerialNumber();
		}
		serialNumberImport_.SerialNumber.SerialNumberId = int.Parse(childElementIfThere.GetAttribute("id"));
		serialNumberImport_.ClearUpdateFlags();
		return serialNumberImport_.SerialNumberImportId;
	}

	public void UpdateSerialNumberImport(SerialNumberImport serialNumberImport_)
	{
		if (serialNumberImport_.SerialNumberImportId == 0)
		{
			throw new Exception("When updating a serial number import, you must use a SerialNumberImport object intended for updates.");
		}
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("serialNumberImportUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElementWithId(xmlElement, "serialNumberImport", serialNumberImport_.SerialNumberImportId);
		if (serialNumberImport_.ModifiedCreationDate)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "creationDate", serialNumberImport_.CreationDate.ToString("yyyy-MM-dd"));
		}
		if (serialNumberImport_.ModifiedQuantity)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", serialNumberImport_.Quantity.ToString());
		}
		if (serialNumberImport_.ModifiedMeasurements)
		{
			foreach (Measurement measurement in serialNumberImport_.Measurements)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "measurement", measurement.ToString());
			}
		}
		if (serialNumberImport_.ModifiedUnitCost)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "unitCost", serialNumberImport_.UnitCost.ToString());
		}
		if (serialNumberImport_.ModifiedIsRemnant)
		{
			xmlElement2.SetAttribute("isRemnant", serialNumberImport_.IsRemnant ? "1" : "0");
		}
		AddUpdateSerialNumberElementsIfNecessary(xmlElement2, serialNumberImport_.SerialNumber);
		ExecuteAndIfNecessaryTraceCommand("Serial number import update", xmlElement.OwnerDocument);
		serialNumberImport_.ClearUpdateFlags();
	}

	public void DeleteSerialNumberImport(int serialNumberImportId_)
	{
		DeleteSerialNumberImports(new int[1] { serialNumberImportId_ });
	}

	public void DeleteSerialNumberImports(IEnumerable<int> serialNumberImportIds_)
	{
		DeleteByIds(serialNumberImportIds_, "serialNumberImport", "Serial Number Import ");
	}

	public SerialNumberInventoryAdjustment GetSerialNumberInventoryAdjustment(int serialNumberInventoryAdjustmentId_)
	{
		List<SerialNumberInventoryAdjustment> serialNumberInventoryAdjustments = GetSerialNumberInventoryAdjustments(new int[1] { serialNumberInventoryAdjustmentId_ });
		if (serialNumberInventoryAdjustments.Count > 0)
		{
			return serialNumberInventoryAdjustments[0];
		}
		return null;
	}

	public List<SerialNumberInventoryAdjustment> GetSerialNumberInventoryAdjustmentsForSerialNumber(int serialNumberId_)
	{
		return GetSerialNumberInventoryAdjustments(null, new int[1] { serialNumberId_ });
	}

	public List<SerialNumberInventoryAdjustment> GetSerialNumberInventoryAdjustmentsForSerialNumbers(IEnumerable<int> serialNumberIds_)
	{
		return GetSerialNumberInventoryAdjustments(null, serialNumberIds_);
	}

	private List<SerialNumberInventoryAdjustment> GetSerialNumberInventoryAdjustments(IEnumerable<int> serialNumberInventoryAdjustmentIds_, IEnumerable<int> serialNumberIds_)
	{
		ValidateConnected();
		List<SerialNumberInventoryAdjustment> list = new List<SerialNumberInventoryAdjustment>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("serialNumberInventoryAdjustmentQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (serialNumberInventoryAdjustmentIds_ != null)
		{
			foreach (int item in serialNumberInventoryAdjustmentIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "serialNumberInventoryAdjustment", item);
			}
		}
		if (serialNumberIds_ != null)
		{
			foreach (int item2 in serialNumberIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "serialNumber", item2);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item3 in ExecuteAndIfNecessaryTraceCommand("Serial number inventory adjustment query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("serialNumberInventoryAdjustmentQuery/serialNumberInventoryAdjustment"))
			{
				list.Add(GetSerialNumberInventoryAdjustmentFromInventoryAdjustmentElement(item3));
			}
		}
		return list;
	}

	public List<SerialNumberInventoryAdjustment> GetSerialNumberInventoryAdjustments(IEnumerable<int> serialNumberInventoryAdjustmentIds_)
	{
		return GetSerialNumberInventoryAdjustments(serialNumberInventoryAdjustmentIds_, null);
	}

	private SerialNumberInventoryAdjustment GetSerialNumberInventoryAdjustmentFromInventoryAdjustmentElement(XmlElement inventoryAdjustmentElement_)
	{
		int serialNumberInventoryAdjustmentId_ = int.Parse(inventoryAdjustmentElement_.GetAttribute("id"));
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryAdjustmentElement_, "description");
		decimal quantity_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryAdjustmentElement_, "quantity"));
		DateTime value = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryAdjustmentElement_, "adjustmentDate")).Value;
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(inventoryAdjustmentElement_, "serialNumber");
		SerialNumber serialNumberFromSerialNumberElement = GetSerialNumberFromSerialNumberElement(childElementIfThere);
		SerialNumberInventoryAdjustment serialNumberInventoryAdjustment = new SerialNumberInventoryAdjustment(serialNumberInventoryAdjustmentId_, value, quantity_, textOfChildIfThere, serialNumberFromSerialNumberElement);
		serialNumberInventoryAdjustment.ClearUpdateFlags();
		return serialNumberInventoryAdjustment;
	}

	public int CreateSerialNumberInventoryAdjustment(SerialNumberInventoryAdjustment serialNumberInventoryAdjustment_)
	{
		if (serialNumberInventoryAdjustment_.SerialNumberInventoryAdjustmentId != 0)
		{
			throw new Exception("When creating a serial number inventory adjustment, you must use a new SerialNumberInventoryAdjustment object");
		}
		return CreateOrUpdateSerialNumberInventoryAdjustment(serialNumberInventoryAdjustment_, create_: true);
	}

	public void UpdateSerialNumberInventoryAdjustment(SerialNumberInventoryAdjustment serialNumberInventoryAdjustment_)
	{
		if (serialNumberInventoryAdjustment_.SerialNumberInventoryAdjustmentId == 0)
		{
			throw new Exception("When updating a serial number inventory adjustment, you must use a SerialNumberInventoryAdjustment object intended to update an adjustment.");
		}
		CreateOrUpdateSerialNumberInventoryAdjustment(serialNumberInventoryAdjustment_, create_: false);
	}

	private int CreateOrUpdateSerialNumberInventoryAdjustment(SerialNumberInventoryAdjustment serialNumberInventoryAdjustment_, bool create_)
	{
		ValidateConnected();
		string arg = (create_ ? "Create" : "Update");
		XmlElement xmlElement = CreateCommandDocument($"serialNumberInventoryAdjustment{arg}");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "serialNumberInventoryAdjustment");
		XmlElement xmlElement3 = AddUpdateSerialNumberElementsIfNecessary(xmlElement2, serialNumberInventoryAdjustment_.SerialNumber);
		if (create_)
		{
			if (xmlElement3 == null)
			{
				xmlElement3 = modInternalXMLHelperFunctions.AppendElement(xmlElement2, "serialNumber");
			}
			xmlElement3.SetAttribute("id", $"{serialNumberInventoryAdjustment_.SerialNumber.SerialNumberId}");
		}
		else
		{
			xmlElement2.SetAttribute("id", $"{serialNumberInventoryAdjustment_.SerialNumberInventoryAdjustmentId}");
			if (xmlElement3 != null && xmlElement3.ChildNodes.Count == 0)
			{
				xmlElement2.RemoveChild(xmlElement3);
			}
		}
		if (serialNumberInventoryAdjustment_.ModifiedDescription)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "description", serialNumberInventoryAdjustment_.Description);
		}
		if (serialNumberInventoryAdjustment_.ModifiedAdjustmentDate)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "adjustmentDate", serialNumberInventoryAdjustment_.AdjustmentDate.ToString("yyyy-MM-dd"));
		}
		if (serialNumberInventoryAdjustment_.ModifiedQuantity)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", serialNumberInventoryAdjustment_.Quantity.ToString());
		}
		XmlElement xmlElement4 = (XmlElement)ExecuteAndIfNecessaryTraceCommand($"Serial number inventory adjustment {arg}", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode($"serialNumberInventoryAdjustment{arg}/*");
		if (create_)
		{
			serialNumberInventoryAdjustment_.SetSerialNumberInventoryAdjustmentId(int.Parse(xmlElement4.GetAttribute("id")));
		}
		serialNumberInventoryAdjustment_.ClearUpdateFlags();
		return serialNumberInventoryAdjustment_.SerialNumberInventoryAdjustmentId;
	}

	public void DeleteSerialNumberInventoryAdjustment(int serialNumberInventoryAdjustmentId_)
	{
		DeleteSerialNumberInventoryAdjustments(new int[1] { serialNumberInventoryAdjustmentId_ });
	}

	public void DeleteSerialNumberInventoryAdjustments(IEnumerable<int> serialNumberInventoryAdjustmentIds_)
	{
		DeleteByIds(serialNumberInventoryAdjustmentIds_, "serialNumberInventoryAdjustment", "Serial Number Inventory Adjustment");
	}

	public PurchaseProductVariantInventoryAdjustment GetPurchaseProductVariantInventoryAdjustment(int purchaseProductVariantInventoryAdjustmentId_)
	{
		List<PurchaseProductVariantInventoryAdjustment> purchaseProductVariantInventoryAdjustments = GetPurchaseProductVariantInventoryAdjustments(new int[1] { purchaseProductVariantInventoryAdjustmentId_ });
		if (purchaseProductVariantInventoryAdjustments.Count > 0)
		{
			return purchaseProductVariantInventoryAdjustments[0];
		}
		return null;
	}

	public List<PurchaseProductVariantInventoryAdjustment> GetPurchaseProductVariantInventoryAdjustments(IEnumerable<int> purchaseProductVariantInventoryAdjustmentIds_)
	{
		ValidateConnected();
		List<PurchaseProductVariantInventoryAdjustment> list = new List<PurchaseProductVariantInventoryAdjustment>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("purchaseProductVariantInventoryAdjustmentQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (purchaseProductVariantInventoryAdjustmentIds_ != null)
		{
			foreach (int item in purchaseProductVariantInventoryAdjustmentIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseProductVariantInventoryAdjustment", item);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item2 in ExecuteAndIfNecessaryTraceCommand("Purchase product variant inventory adjustment query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("purchaseProductVariantInventoryAdjustmentQuery/purchaseProductVariantInventoryAdjustment"))
			{
				list.Add(GetPurchaseProductVariantInventoryAdjustmentFromInventoryAdjustmentElement(item2));
			}
		}
		return list;
	}

	private PurchaseProductVariantInventoryAdjustment GetPurchaseProductVariantInventoryAdjustmentFromInventoryAdjustmentElement(XmlElement inventoryAdjustmentElement_)
	{
		int purchaseProductVariantInventoryAdjustmentId_ = int.Parse(inventoryAdjustmentElement_.GetAttribute("id"));
		string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryAdjustmentElement_, "description");
		decimal quantity_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryAdjustmentElement_, "quantity"));
		DateTime value = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(inventoryAdjustmentElement_, "adjustmentDate")).Value;
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(inventoryAdjustmentElement_, "purchaseProductVariant");
		PurchaseProductVariant purchaseProductVariant_ = (PurchaseProductVariant)GetProductVariantFromPVElement(childElementIfThere, purchaseProducts_: true);
		PurchaseProductVariantInventoryAdjustment purchaseProductVariantInventoryAdjustment = new PurchaseProductVariantInventoryAdjustment(purchaseProductVariantInventoryAdjustmentId_, value, quantity_, textOfChildIfThere, purchaseProductVariant_);
		purchaseProductVariantInventoryAdjustment.ClearUpdateFlags();
		return purchaseProductVariantInventoryAdjustment;
	}

	public int CreatePurchaseProductVariantInventoryAdjustment(PurchaseProductVariantInventoryAdjustment purchaseProductVariantInventoryAdjustment_)
	{
		if (purchaseProductVariantInventoryAdjustment_.PurchaseProductVariantInventoryAdjustmentId != 0)
		{
			throw new Exception("When creating a purchase product variant inventory adjustment, you must use a new PurchaseProductVariantInventoryAdjustment object");
		}
		return CreateOrUpdatePurchaseProductVariantInventoryAdjustment(purchaseProductVariantInventoryAdjustment_, create_: true);
	}

	public void UpdatePurchaseProductVariantInventoryAdjustment(PurchaseProductVariantInventoryAdjustment purchaseProductVariantInventoryAdjustment_)
	{
		if (purchaseProductVariantInventoryAdjustment_.PurchaseProductVariantInventoryAdjustmentId == 0)
		{
			throw new Exception("When updating a purchase product variant inventory adjustment, you must use a PurchaseProductVariantInventoryAdjustment object intended to update an adjustment.");
		}
		CreateOrUpdatePurchaseProductVariantInventoryAdjustment(purchaseProductVariantInventoryAdjustment_, create_: false);
	}

	private int CreateOrUpdatePurchaseProductVariantInventoryAdjustment(PurchaseProductVariantInventoryAdjustment purchaseProductVariantInventoryAdjustment_, bool create_)
	{
		ValidateConnected();
		string arg = (create_ ? "Create" : "Update");
		XmlElement xmlElement = CreateCommandDocument($"purchaseProductVariantInventoryAdjustment{arg}");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "purchaseProductVariantInventoryAdjustment");
		if (create_)
		{
			if (purchaseProductVariantInventoryAdjustment_.PrepedToCreateByPVId)
			{
				modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "purchaseProductVariant", purchaseProductVariantInventoryAdjustment_.PurchaseProductVariantId);
			}
			else
			{
				XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement2, "purchaseProductVariantByValues");
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "purchaseProduct", purchaseProductVariantInventoryAdjustment_.PurchaseProductId);
				foreach (ProductAttributeValue productAttributeValue in purchaseProductVariantInventoryAdjustment_.ProductAttributeValues)
				{
					if (productAttributeValue.ProductAttributeValueId > 0)
					{
						modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "productAttributeValue", productAttributeValue.ProductAttributeValueId);
						continue;
					}
					XmlElement parentNode_2 = modInternalXMLHelperFunctions.AppendElement(parentNode_, "productAttributeValueValue");
					if (productAttributeValue.ProductAttributeTypeId > 0)
					{
						modInternalXMLHelperFunctions.AppendElementWithId(parentNode_2, "productAttributeType", productAttributeValue.ProductAttributeTypeId);
					}
					else
					{
						modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "productAttributeTypeName", productAttributeValue.ProductAttributeTypeName);
					}
					modInternalXMLHelperFunctions.AppendTextElementIfIsValue(parentNode_2, "value", productAttributeValue.Value);
				}
			}
		}
		else
		{
			xmlElement2.SetAttribute("id", purchaseProductVariantInventoryAdjustment_.PurchaseProductVariantInventoryAdjustmentId.ToString());
		}
		if (purchaseProductVariantInventoryAdjustment_.ModifiedDescription)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "description", purchaseProductVariantInventoryAdjustment_.Description);
		}
		if (purchaseProductVariantInventoryAdjustment_.ModifiedAdjustmentDate)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "adjustmentDate", purchaseProductVariantInventoryAdjustment_.AdjustmentDate.ToString("yyyy-MM-dd"));
		}
		if (purchaseProductVariantInventoryAdjustment_.ModifiedQuantity)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", purchaseProductVariantInventoryAdjustment_.Quantity.ToString());
		}
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand($"Purchase product variant inventory adjustment {arg}", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode($"purchaseProductVariantInventoryAdjustment{arg}/*");
		if (create_)
		{
			purchaseProductVariantInventoryAdjustment_.PurchaseProductVariantInventoryAdjustmentId = int.Parse(xmlElement3.GetAttribute("id"));
		}
		purchaseProductVariantInventoryAdjustment_.ClearUpdateFlags();
		return purchaseProductVariantInventoryAdjustment_.PurchaseProductVariantInventoryAdjustmentId;
	}

	public void DeletePurchaseProductVariantInventoryAdjustment(int purchaseProductVariantInventoryAdjustmentId_)
	{
		DeletePurchaseProductVariantInventoryAdjustments(new int[1] { purchaseProductVariantInventoryAdjustmentId_ });
	}

	public void DeletePurchaseProductVariantInventoryAdjustments(IEnumerable<int> purchaseProductVariantInventoryAdjustmentIds_)
	{
		DeleteByIds(purchaseProductVariantInventoryAdjustmentIds_, "purchaseProductVariantInventoryAdjustment", "Purchase Product Variant Inventory Adjustment");
	}

	public SerialNumberRemnant GetSerialNumberRemnant(int serialNumberRemnantId_)
	{
		List<SerialNumberRemnant> serialNumberRemnants = GetSerialNumberRemnants(new int[1] { serialNumberRemnantId_ });
		if (serialNumberRemnants.Count > 0)
		{
			return serialNumberRemnants[0];
		}
		return null;
	}

	private List<SerialNumberRemnant> GetSerialNumberRemnants(IEnumerable<int> serialNumberRemnantIds_, IEnumerable<int> parentSerialNumberIds_)
	{
		ValidateConnected();
		List<SerialNumberRemnant> list = new List<SerialNumberRemnant>();
		bool flag = true;
		XmlElement xmlElement = CreateCommandDocument("serialNumberRemnantQuery");
		XmlElement parentNode_ = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (serialNumberRemnantIds_ != null)
		{
			foreach (int item in serialNumberRemnantIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "serialNumberRemnant", item);
			}
		}
		if (parentSerialNumberIds_ != null)
		{
			foreach (int item2 in parentSerialNumberIds_)
			{
				flag = false;
				modInternalXMLHelperFunctions.AppendElementWithId(parentNode_, "parentSerialNumber", item2);
			}
		}
		if (!flag)
		{
			ValidateConnected();
			modInternalXMLHelperFunctions.AppendElement(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), "all");
			foreach (XmlElement item3 in ExecuteAndIfNecessaryTraceCommand("Serial number remnant query", xmlElement.OwnerDocument).DocumentElement.SelectNodes("serialNumberRemnantQuery/serialNumberRemnant"))
			{
				list.Add(GetRemnantFromRemnantElement(item3));
			}
		}
		return list;
	}

	public List<SerialNumberRemnant> GetSerialNumberRemnants(IEnumerable<int> serialNumberRemnantIds_)
	{
		return GetSerialNumberRemnants(serialNumberRemnantIds_, null);
	}

	public List<SerialNumberRemnant> GetSerialNumberRemnantsOfParent(IEnumerable<int> parentSerialNumberIds_)
	{
		return GetSerialNumberRemnants(null, parentSerialNumberIds_);
	}

	private SerialNumberRemnant GetRemnantFromRemnantElement(XmlElement remnantElement_)
	{
		int serialNumberRemnantId_ = int.Parse(remnantElement_.GetAttribute("id"));
		int value = GetNullableIntFromAttribute(remnantElement_, "parentSerialNumberId", requireValue_: true, ".").Value;
		decimal unitCost_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(remnantElement_, "unitCost"));
		decimal quantity_ = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(remnantElement_, "quantity"));
		DateTime value2 = ParseDate(modInternalXMLHelperFunctions.GetTextOfChildIfThere(remnantElement_, "creationDate")).Value;
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(remnantElement_, "serialNumber");
		SerialNumber serialNumberFromSerialNumberElement = GetSerialNumberFromSerialNumberElement(childElementIfThere);
		SerialNumberRemnant serialNumberRemnant = new SerialNumberRemnant(serialNumberRemnantId_, value, unitCost_, value2, serialNumberFromSerialNumberElement, quantity_);
		foreach (XmlElement item in remnantElement_.SelectNodes("measurement"))
		{
			serialNumberRemnant.Measurements.AddMeasurement(new Measurement(decimal.Parse(item.InnerText)));
		}
		serialNumberRemnant.ClearUpdateFlags();
		return serialNumberRemnant;
	}

	public int CreateSerialNumberRemnant(SerialNumberRemnant serialNumberRemnant_)
	{
		if (serialNumberRemnant_.SerialNumberRemnantId != 0)
		{
			throw new Exception("When creating a serial number remnant, you must use a new SerialNumberRemnant object");
		}
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("serialNumberRemnantCreate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "serialNumberRemnant");
		xmlElement2.SetAttribute("parentSerialNumberId", serialNumberRemnant_.ParentSerialNumberId.ToString());
		if (serialNumberRemnant_.ModifiedCreationDate)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "creationDate", serialNumberRemnant_.CreationDate.ToString("yyyy-MM-dd"));
		}
		if (serialNumberRemnant_.ModifiedQuantity)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", serialNumberRemnant_.Quantity.ToString());
		}
		if (serialNumberRemnant_.ModifiedMeasurements)
		{
			foreach (Measurement measurement in serialNumberRemnant_.Measurements)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "measurement", measurement.ToString());
			}
		}
		if (serialNumberRemnant_.ModifiedUnitCost)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "unitCost", serialNumberRemnant_.UnitCost.ToString());
		}
		AddUpdateSerialNumberElementsIfNecessary(xmlElement2, serialNumberRemnant_.SerialNumber);
		XmlElement xmlElement3 = (XmlElement)ExecuteAndIfNecessaryTraceCommand("Serial number remnant create", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("serialNumberRemnantCreate/*");
		serialNumberRemnant_.SerialNumberRemnantId = int.Parse(xmlElement3.GetAttribute("id"));
		XmlElement childElementIfThere = modInternalXMLHelperFunctions.GetChildElementIfThere(xmlElement3, "serialNumber");
		if (serialNumberRemnant_.SerialNumber == null)
		{
			serialNumberRemnant_.SerialNumber = new SerialNumber();
		}
		serialNumberRemnant_.SerialNumber.SerialNumberId = int.Parse(childElementIfThere.GetAttribute("id"));
		serialNumberRemnant_.ClearUpdateFlags();
		return serialNumberRemnant_.SerialNumberRemnantId;
	}

	public void UpdateSerialNumberRemnant(SerialNumberRemnant serialNumberRemnant_)
	{
		if (serialNumberRemnant_.SerialNumberRemnantId == 0)
		{
			throw new Exception("When updating a serial number remnant, you must use a SerialNumberRemnant object intended for updates.");
		}
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("serialNumberRemnantUpdate");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "serialNumberRemnant");
		xmlElement2.SetAttribute("id", serialNumberRemnant_.SerialNumberRemnantId.ToString());
		if (serialNumberRemnant_.ModifiedCreationDate)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "creationDate", serialNumberRemnant_.CreationDate.ToString("yyyy-MM-dd"));
		}
		if (serialNumberRemnant_.ModifiedQuantity)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "quantity", serialNumberRemnant_.Quantity.ToString());
		}
		if (serialNumberRemnant_.ModifiedMeasurements)
		{
			foreach (Measurement measurement in serialNumberRemnant_.Measurements)
			{
				modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "measurement", measurement.ToString());
			}
		}
		if (serialNumberRemnant_.ModifiedUnitCost)
		{
			modInternalXMLHelperFunctions.AppendTextElementIfIsValue(xmlElement2, "unitCost", serialNumberRemnant_.UnitCost.ToString());
		}
		AddUpdateSerialNumberElementsIfNecessary(xmlElement2, serialNumberRemnant_.SerialNumber);
		ExecuteAndIfNecessaryTraceCommand("Serial number remnant update", xmlElement.OwnerDocument);
		serialNumberRemnant_.ClearUpdateFlags();
	}

	public void DeleteSerialNumberRemnant(int serialNumberRemnantId_)
	{
		DeleteSerialNumberRemnants(new int[1] { serialNumberRemnantId_ });
	}

	public void DeleteSerialNumberRemnants(IEnumerable<int> serialNumberRemnantIds_)
	{
		DeleteByIds(serialNumberRemnantIds_, "serialNumberRemnant", "Serial Number Remnant");
	}

	public List<UnreceivedSerialNumber> GetUnreceivedSerialNumbers(IEnumerable<int> unreceivedSerialNumberIds_)
	{
		return GetUnreceivedSerialNumbers(unreceivedSerialNumberIds_, null, null);
	}

	public UnreceivedSerialNumber GetUnreceivedSerialNumber(int unreceivedSerialNumberId_)
	{
		List<UnreceivedSerialNumber> unreceivedSerialNumbers = GetUnreceivedSerialNumbers(new int[1] { unreceivedSerialNumberId_ }, null, null);
		if (unreceivedSerialNumbers.Count > 0)
		{
			return unreceivedSerialNumbers[0];
		}
		return null;
	}

	public List<UnreceivedSerialNumber> GetUnreceivedSerialNumbersOfPurchaseOrders(IEnumerable<int> purchaseOrderIds_)
	{
		return GetUnreceivedSerialNumbers(null, purchaseOrderIds_, null);
	}

	public List<UnreceivedSerialNumber> GetUnreceivedSerialNumbersOfPurchaseOrder(int purchaseOrderId_)
	{
		return GetUnreceivedSerialNumbers(null, new int[1] { purchaseOrderId_ }, null);
	}

	public List<UnreceivedSerialNumber> GetUnreceivedSerialNumbersOfPurchaseOrderLines(IEnumerable<int> purchaseOrderLineIds_)
	{
		return GetUnreceivedSerialNumbers(null, null, purchaseOrderLineIds_);
	}

	public List<UnreceivedSerialNumber> GetUnreceivedSerialNumbersOfPurchaseOrderLine(int purchaseOrderLineId_)
	{
		return GetUnreceivedSerialNumbers(null, null, new int[1] { purchaseOrderLineId_ });
	}

	public SerialNumber GetSerialNumber(int serialNumberId_)
	{
		List<SerialNumber> serialNumbers = GetSerialNumbers(new int[1] { serialNumberId_ });
		if (serialNumbers.Count == 0)
		{
			return null;
		}
		return serialNumbers[0];
	}

	public List<SerialNumber> GetSerialNumbers(IEnumerable<int> serialNumberIds_)
	{
		return GetSerialNumbers(serialNumberIds_, queryById_: true, null, null);
	}

	public List<SerialNumber> GetSerialNumbers(SerialNumberFilter serialNumberFilter_, PagingOptions pagingOptions_)
	{
		return GetSerialNumbers(null, queryById_: false, serialNumberFilter_, pagingOptions_);
	}

	private List<SerialNumber> GetSerialNumbers(IEnumerable<int> serialNumberIds_, bool queryById_, SerialNumberFilter serialNumberFilter_, PagingOptions pagingOptions_)
	{
		List<SerialNumber> list = new List<SerialNumber>();
		bool flag = queryById_;
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("serialNumberQuery");
		XmlElement xmlElement2 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "filter");
		if (pagingOptions_ != null)
		{
			AppendPagingSpec(xmlElement, pagingOptions_.FirstRecord, pagingOptions_.PageSize);
		}
		XmlElement xmlElement3 = modInternalXMLHelperFunctions.AppendElement(xmlElement, "include");
		modInternalXMLHelperFunctions.AppendElement(xmlElement3, "all");
		if (true)
		{
			AddObjectCustomFieldIncludeElements(xmlElement3, "serialNumber");
		}
		if (queryById_)
		{
			if (serialNumberIds_ != null)
			{
				foreach (int item in serialNumberIds_)
				{
					flag = false;
					modInternalXMLHelperFunctions.AppendElementWithId(xmlElement2, "serialNumber", item);
				}
			}
		}
		else
		{
			AppendNecessaryCustomFilters(xmlElement2, serialNumberFilter_.CustomFieldFilters);
			AppendBuiltInTextFilters(xmlElement2, serialNumberFilter_.TextFilters);
			AppendBuiltInListOfValuesFilters(xmlElement2, serialNumberFilter_.ListOfValuesFilters);
		}
		if (!flag)
		{
			XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("Serial Number query", xmlElement.OwnerDocument);
			if (pagingOptions_ != null && pagingOptions_.TotalRecords.HasValue)
			{
				pagingOptions_.TotalRecords = Convert.ToInt32(modInternalXMLHelperFunctions.GetChildElementIfThere(xmlDocument.DocumentElement, "serialNumberQuery").GetAttribute("totalRecords"));
			}
			foreach (XmlElement item2 in xmlDocument.DocumentElement.SelectNodes("serialNumberQuery/serialNumber"))
			{
				list.Add(GetSerialNumberFromSerialNumberElement(item2));
			}
		}
		return list;
	}

	private SerialNumber GetSerialNumberFromSerialNumberElement(XmlElement serialNumberElement_)
	{
		SerialNumber serialNumber = new SerialNumber(int.Parse(serialNumberElement_.GetAttribute("id")));
		serialNumber.SerialNumberId = GetNullableIntFromAttribute(serialNumberElement_, "id", requireValue_: true, ".").Value;
		serialNumber.SerialNumberName = modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "name");
		serialNumber.Description = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "description"));
		serialNumber.BatchNumber = CanonicalizeMultiLineTextFromResponse(modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "batchNumber"));
		serialNumber.SetInventoryLocation(GetNullableIntFromAttribute(serialNumberElement_, "id", requireValue_: false, "inventoryLocation"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "inventoryLocation/name", null));
		serialNumber.SetPurchaseProduct(GetNullableIntFromAttribute(serialNumberElement_, "id", requireValue_: true, "purchaseProduct").Value, modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "purchaseProduct/name", null));
		serialNumber.SetProductVariant(GetNullableIntFromAttribute(serialNumberElement_, "id", requireValue_: true, "purchaseProductVariant").Value, modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "purchaseProductVariant/name", null));
		serialNumber.CustomFieldValues = GetCustomFieldValuesForObject(serialNumberElement_);
		serialNumber.Quantity = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "quantity"));
		serialNumber.Balance = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "balance"));
		serialNumber.UnitCost = Convert.ToDecimal(modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "unitCost"));
		serialNumber.SetUnitOfMeasure(GetNullableIntFromAttribute(serialNumberElement_, "id", requireValue_: true, "unitOfMeasure").Value, modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "unitOfMeasure/name"));
		serialNumber.MeasurementDescription = modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "measurementDescription");
		foreach (XmlElement item in serialNumberElement_.SelectNodes("measurement"))
		{
			serialNumber.Measurements.AddMeasurement(new Measurement(decimal.Parse(item.InnerText)));
		}
		switch (modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "remnantType"))
		{
		case "Not Remnant":
			serialNumber.RemnantType = SerialNumber.RemnantType_Enum.NotRemnant;
			break;
		case "Remnant":
			serialNumber.RemnantType = SerialNumber.RemnantType_Enum.Remnant;
			break;
		case "Imported Remnant":
			serialNumber.RemnantType = SerialNumber.RemnantType_Enum.Import;
			break;
		}
		switch (modInternalXMLHelperFunctions.GetTextOfChildIfThere(serialNumberElement_, "source/type"))
		{
		case "Received":
			serialNumber.SerialNumberSourceType = SerialNumber.SerialNumberSourceType_Enum.Received;
			break;
		case "Unreceived":
			serialNumber.SerialNumberSourceType = SerialNumber.SerialNumberSourceType_Enum.Unreceived;
			break;
		case "Import":
			serialNumber.SerialNumberSourceType = SerialNumber.SerialNumberSourceType_Enum.Import;
			break;
		case "Remnant":
			serialNumber.SerialNumberSourceType = SerialNumber.SerialNumberSourceType_Enum.Remnant;
			break;
		}
		serialNumber.SerialNumberSourceId = GetNullableIntFromAttribute(serialNumberElement_, "id", requireValue_: true, "source").Value;
		serialNumber.ClearUpdateFlags();
		return serialNumber;
	}

	public void UpdateSerialNumber(SerialNumber serialNumber_)
	{
		ValidateConnected();
		ValidatePositiveId(serialNumber_.SerialNumberId, "Serial Number", "Update Serial Number");
		XmlElement xmlElement = CreateCommandDocument("serialNumberUpdate");
		AddUpdateSerialNumberElementsIfNecessary(xmlElement, serialNumber_).SetAttribute("id", serialNumber_.SerialNumberId.ToString());
		ExecuteAndIfNecessaryTraceCommand("serialNumber update", xmlElement.OwnerDocument);
		serialNumber_.ClearUpdateFlags();
	}

	private bool IsRequestContentEncodingAccepted(string encoding_)
	{
		return m_acceptedRequestContentEncodings.ContainsKey(encoding_);
	}

	internal decimal? ParseDecimalIfThere(string string_)
	{
		if (string_ != null && string_.Length > 0)
		{
			return decimal.Parse(string_);
		}
		return null;
	}

	internal static DateTime? ParseDate(string dateOnlyString_)
	{
		if (dateOnlyString_ != null && dateOnlyString_.Length > 0)
		{
			string text = dateOnlyString_.Replace("-", "/") + " 00:00:00";
			DateTime dateTime = default(DateTime);
			try
			{
				dateTime = DateTime.Parse(text);
			}
			catch (Exception)
			{
				throw new Exception("Failed to parse \"" + text + "\" as a date.");
			}
			return dateTime;
		}
		return null;
	}

	internal static DateTime? ParseDateTime(string dateTimeString_)
	{
		if (dateTimeString_ != null && dateTimeString_.Length > 0)
		{
			string text = dateTimeString_.Replace("-", "/").Replace("T", " ");
			DateTime dateTime = default(DateTime);
			try
			{
				dateTime = DateTime.Parse(text);
			}
			catch (Exception)
			{
				throw new Exception("Failed to parse \"" + text + "\" as a datetime.");
			}
			return dateTime;
		}
		return null;
	}

	internal static DateTime? ParseHMTime(string timeOnlyString_)
	{
		if (timeOnlyString_ != null && timeOnlyString_.Length > 0)
		{
			return DateTime.Parse("1900/01/01 " + timeOnlyString_);
		}
		return null;
	}

	public Connection(string url_ = "", string userName_ = "", string password_ = "", ICommandTracer commandTracer_ = null, bool compressRequests_ = true, bool compressResponses_ = true, string applicationName_ = "")
	{
		Url = url_;
		UserName = userName_;
		Password = password_;
		CommandTracer = commandTracer_;
		CompressRequests = compressRequests_;
		CompressResponses = compressResponses_;
		ApplicationName = applicationName_;
	}

	private void SetSessionId(string sessionId_, XmlElement acceptedRequestContentEncodingsElement_)
	{
		if (acceptedRequestContentEncodingsElement_ == null)
		{
			m_acceptedRequestContentEncodings.Clear();
		}
		else
		{
			foreach (XmlElement item in acceptedRequestContentEncodingsElement_.SelectNodes("encoding"))
			{
				string innerText = item.InnerText;
				if (innerText.Length > 0 && !m_acceptedRequestContentEncodings.ContainsKey(innerText))
				{
					m_acceptedRequestContentEncodings.Add(innerText, innerText);
				}
			}
		}
		SessionId = sessionId_;
	}

	private XmlDocument ExecuteCommand(XmlDocument commandDocument_, bool testForErrorResponse_, bool rawUserAgent_)
	{
		XmlDocument xmlDocument = new XmlDocument();
		bool flag = false;
		do
		{
			flag = false;
			if (!string.IsNullOrEmpty(SessionId))
			{
				commandDocument_.DocumentElement.SetAttribute("sessionId", SessionId);
			}
			string xml = ExecuteCommandSynchronous(commandDocument_.OuterXml, rawUserAgent_);
			xmlDocument.PreserveWhitespace = true;
			xmlDocument.LoadXml(xml);
			if (!testForErrorResponse_)
			{
				continue;
			}
			try
			{
				TestForErrorResponse(xmlDocument);
			}
			catch (APIException ex)
			{
				if (AutoRefreshOnTimeout && ex.APIErrorCode == APIException.APIErrorCodes_Enum.SessionTimedOut && commandDocument_.DocumentElement.SelectSingleNode("sessionLogout") == null)
				{
					Connect();
					flag = true;
					continue;
				}
				throw ex;
			}
		}
		while (flag);
		return xmlDocument;
	}

	public XmlDocument ExecuteCommand(XmlDocument commandDocument_, bool testForErrorResponse_)
	{
		return ExecuteCommand(commandDocument_, testForErrorResponse_, rawUserAgent_: true);
	}

	public XmlElement CreateCommandDocument(string commandName_, string apiVersion_ = "5")
	{
		int? prereleaseVersion_ = null;
		if (apiVersion_ == "5")
		{
			prereleaseVersion_ = DEFAULT_PRERELEASE_API_VERSION;
		}
		return CreateCommandDocument(commandName_, apiVersion_, prereleaseVersion_);
	}

	public XmlElement CreateCommandDocument(string commandName_, string apiVersion_, int? prereleaseVersion_)
	{
		XmlDocument xmlDocument = new XmlDocument();
		xmlDocument.AppendChild(xmlDocument.CreateElement("MorawareCommand"));
		xmlDocument.DocumentElement.SetAttribute("version", apiVersion_);
		if (prereleaseVersion_.HasValue)
		{
			xmlDocument.DocumentElement.SetAttribute("prereleaseVersion", prereleaseVersion_.ToString());
		}
		if (SessionId.Length > 0)
		{
			xmlDocument.DocumentElement.SetAttribute("sessionId", SessionId);
		}
		else if (commandName_ != "sessionCreate")
		{
			throw new Exception("Everything requires a session except 'sessionCreate'!");
		}
		XmlElement result = modInternalXMLHelperFunctions.AppendElement(xmlDocument.DocumentElement, commandName_);
		if (commandName_ == "sessionCreate")
		{
			xmlDocument.DocumentElement.SetAttribute("userName", UserName);
			xmlDocument.DocumentElement.SetAttribute("password", Password);
		}
		return result;
	}

	public void Disconnect()
	{
		if (Connected)
		{
			try
			{
				ExecuteCommand(CreateCommandDocument("sessionLogout").OwnerDocument, testForErrorResponse_: false, rawUserAgent_: false);
			}
			catch (Exception)
			{
			}
			SetSessionId("", null);
		}
	}

	private void CacheVersionInfo()
	{
		if (string.IsNullOrEmpty(_jobTrackerAPIVersion))
		{
			_jobTrackerAPIVersion = $"{GetType().Assembly.GetName().Version.Major}.{GetType().Assembly.GetName().Version.Minor}";
			_dotNetVersion = Environment.Version.ToString();
		}
	}

	private string ExecuteCommandSynchronous(string command_, bool rawUserAgent_)
	{
		HttpWebRequest httpWebRequest = modHTTPConnectionUtils.CreateHttpWebRequest(Url, modHTTPConnectionUtils.ContentType_Enum.ctTextXML);
		if (CompressResponses)
		{
			httpWebRequest.AutomaticDecompression = DecompressionMethods.GZip;
		}
		CacheVersionInfo();
		httpWebRequest.UserAgent = string.Format("JobTrackerAPI{0}/{1} (.NET CLR {2})", rawUserAgent_ ? "Raw" : "Obj", _jobTrackerAPIVersion, _dotNetVersion) + string.Format("{0}", string.IsNullOrEmpty(ApplicationName) ? "" : $" {ApplicationName}");
		bool flag = CompressRequests & IsRequestContentEncodingAccepted("gzip");
		if (flag)
		{
			httpWebRequest.Headers.Add(HttpRequestHeader.ContentEncoding, "gzip");
		}
		using (Stream stream = httpWebRequest.GetRequestStream())
		{
			if (flag)
			{
				using GZipStream stream2 = new GZipStream(stream, CompressionMode.Compress);
				using StreamWriter streamWriter = new StreamWriter(stream2);
				streamWriter.Write(command_);
			}
			else
			{
				using StreamWriter streamWriter2 = new StreamWriter(stream);
				streamWriter2.Write(command_);
			}
		}
		using StreamReader streamReader = new StreamReader(((HttpWebResponse)httpWebRequest.GetResponse()).GetResponseStream());
		return streamReader.ReadToEnd();
	}

	internal XmlDocument ExecuteCommand(string command_)
	{
		XmlDocument xmlDocument = null;
		bool flag = false;
		do
		{
			try
			{
				if (flag)
				{
					Connect();
				}
				flag = false;
				if (Connected)
				{
					int num = command_.IndexOf("sessionId");
					num = command_.IndexOf('"', num + 1) + 1;
					int startIndex = command_.IndexOf('"', num);
					command_ = command_.Substring(0, num) + SessionId + command_.Substring(startIndex);
				}
				string xml = ExecuteCommandSynchronous(command_, rawUserAgent_: false);
				xmlDocument = new XmlDocument
				{
					PreserveWhitespace = true
				};
				xmlDocument.LoadXml(xml);
				TestForErrorResponse(xmlDocument);
			}
			catch (APIException ex)
			{
				APIException.APIErrorCodes_Enum aPIErrorCode = ex.APIErrorCode;
				if (aPIErrorCode == APIException.APIErrorCodes_Enum.SessionTimedOut)
				{
					if (AutoRefreshOnTimeout)
					{
						SetSessionId("", null);
						flag = true;
						continue;
					}
					throw ex;
				}
				throw ex;
			}
		}
		while (flag);
		return xmlDocument;
	}

	public void Connect()
	{
		if (!string.IsNullOrEmpty(SessionId))
		{
			try
			{
				ExecuteCommand(CreateCommandDocument("sessionLogout").OwnerDocument.OuterXml);
			}
			catch (APIException ex)
			{
				if (ex.APIErrorCode != APIException.APIErrorCodes_Enum.SessionTimedOut)
				{
					MessageBox.Show("Failed to disconnect prior to connecting:" + Environment.NewLine + ex.Message);
				}
			}
			catch (Exception ex2)
			{
				MessageBox.Show("Failed to disconnect prior to connecting:" + Environment.NewLine + ex2.Message);
			}
			SetSessionId("", null);
		}
		XmlElement xmlElement = CreateCommandDocument("sessionCreate");
		XmlDocument xmlDocument = ExecuteCommand(xmlElement.OwnerDocument.OuterXml);
		if (xmlDocument != null)
		{
			XmlElement xmlElement2 = (XmlElement)xmlDocument.SelectSingleNode("MorawareResponse/sessionCreate/session");
			if (xmlElement2 == null)
			{
				throw new Exception("sessionCreate response contained no session info:  \r\n" + xmlDocument.OuterXml);
			}
			SetSessionId(xmlElement2.GetAttribute("id") ?? "", (XmlElement)xmlElement2.SelectSingleNode("acceptedRequestContentEncodings"));
			if (SessionId.Length == 0)
			{
				throw new Exception("session element did not include a session id:  \r\n" + xmlElement2.OuterXml);
			}
		}
	}

	private void TestForErrorResponse(XmlDocument doc_)
	{
		XmlElement xmlElement = (XmlElement)doc_.SelectSingleNode("error");
		XmlNodeList xmlNodeList = null;
		if (xmlElement == null)
		{
			xmlNodeList = doc_.SelectNodes("(*/error)|(*/*/error)");
			if (xmlNodeList.Count > 0)
			{
				xmlElement = (XmlElement)xmlNodeList.Item(0);
			}
		}
		if (xmlElement == null)
		{
			return;
		}
		string text = modInternalXMLHelperFunctions.GetTextOfChildIfThere(xmlElement, "description");
		string attribute = xmlElement.GetAttribute("errorCode");
		if (attribute.Length > 0)
		{
			string attribute2 = xmlElement.GetAttribute("errorCodeDescription");
			text = $"Error code:  {attribute2} (Error Id = {attribute})\r\n" + text;
		}
		if (text.Length == 0)
		{
			text = "Error from server:\r\n" + xmlElement.OuterXml;
		}
		if (IncludeStackTraceInDescription)
		{
			string textOfChildIfThere = modInternalXMLHelperFunctions.GetTextOfChildIfThere(xmlElement, "stackTrace");
			if (textOfChildIfThere.Length > 0)
			{
				text = text + "\r\n\r\nStack Trace:\r\n" + textOfChildIfThere;
			}
		}
		APIException.APIErrorCodes_Enum apiErrorCode_ = (APIException.APIErrorCodes_Enum)0;
		if (APIException.ConvertToAPIErrorCode(attribute, ref apiErrorCode_))
		{
			if (apiErrorCode_ == APIException.APIErrorCodes_Enum.UnsupportedVersion)
			{
				throw new UnsupportedAPIVersionException(doc_, text, xmlElement);
			}
			throw new APIException(doc_, text, apiErrorCode_);
		}
		throw new Exception(text);
	}

	public ServerAPIVersion GetServerAPIVersion()
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("apiVersionQuery");
		XmlElement obj = (XmlElement)ExecuteAndIfNecessaryTraceCommand("API version query", xmlElement.OwnerDocument).DocumentElement.SelectSingleNode("apiVersionQuery");
		int minSupportedVersion_ = int.Parse(obj.GetAttribute("minSupportedVersion"));
		int currentVersion_ = int.Parse(obj.GetAttribute("currentVersion"));
		int? nullableIntFromAttribute = GetNullableIntFromAttribute(obj, "prereleaseVersion");
		return new ServerAPIVersion(minSupportedVersion_, currentVersion_, nullableIntFromAttribute);
	}

	private void AppendPagingSpec(XmlElement parentElement_, int firstRecord_, int recordCount_)
	{
		XmlElement xmlElement = modInternalXMLHelperFunctions.AppendElement(parentElement_, "pagingSpec");
		xmlElement.SetAttribute("firstRecord", firstRecord_.ToString());
		xmlElement.SetAttribute("pageSize", recordCount_.ToString());
	}

	private string CanonicalizeMultiLineTextFromResponse(string string_)
	{
		if (string_ != null)
		{
			string_ = string_.Replace(Environment.NewLine, "\n").Replace("\r", "\n").Replace("\n", Environment.NewLine);
		}
		return string_;
	}

	private void ValidateConnected()
	{
		if (!Connected)
		{
			throw new Exception("Not Connected!");
		}
	}

	internal static bool GetBooleanFromAttribute(XmlElement element_, string attrName_, bool defaultValue_ = false)
	{
		string attribute = element_.GetAttribute(attrName_);
		if ("" == attribute)
		{
			return defaultValue_;
		}
		return attribute == "1";
	}

	private void ValidatePositiveId(int id_, string strIdTypeName_, string strQueryTypeName_)
	{
		if (id_ < 1)
		{
			throw new APIException($"Invalid {strIdTypeName_} Id ({id_}) given for {strQueryTypeName_} Query.", APIException.APIErrorCodes_Enum.InvalidRequestDocument);
		}
	}

	private void AppendElementWithIdForCreateOrUpdateIfNecessary(XmlElement parentElement_, DefaultJobTemplateContainer defaultJobTemplates_, bool create_)
	{
		if (defaultJobTemplates_ == null)
		{
			return;
		}
		foreach (DefaultJobTemplate item in defaultJobTemplates_)
		{
			JobTemplate jobTemplate = item.JobTemplate;
			if ((!create_ || jobTemplate != null) && item.Modified)
			{
				XmlElement xmlElement = modInternalXMLHelperFunctions.AppendElement(parentElement_, "defaultJobTemplate");
				xmlElement.SetAttribute("processId", item.ProcessId.ToString());
				if (jobTemplate != null)
				{
					xmlElement.SetAttribute("id", jobTemplate.JobTemplateId.ToString());
				}
			}
		}
	}

	private void DeleteByIds<T>(IEnumerable<T> ids_, string xmlTagName_, string descriptiveName_, string commandAttributeName_ = null, string commandAttributeValue_ = null)
	{
		XmlElement xmlElement = CreateCommandDocument(xmlTagName_ + "Delete");
		if (commandAttributeName_ != null && commandAttributeName_.Length > 0)
		{
			if (commandAttributeValue_ == null)
			{
				commandAttributeValue_ = "";
			}
			xmlElement.SetAttribute(commandAttributeName_, commandAttributeValue_);
		}
		bool flag = false;
		if (ids_ != null)
		{
			foreach (T item in ids_)
			{
				modInternalXMLHelperFunctions.AppendElement(xmlElement, xmlTagName_).SetAttribute("id", item.ToString());
				flag = true;
			}
		}
		if (flag)
		{
			ValidateConnected();
			ExecuteAndIfNecessaryTraceCommand($"{descriptiveName_} delete", xmlElement.OwnerDocument);
		}
	}

	internal static int? GetNullableIntFromAttribute(XmlElement element_, string attrName_, bool requireValue_ = false, string xpath_ = null)
	{
		int? result = null;
		if (element_ != null && xpath_ != null && xpath_.Length > 0)
		{
			element_ = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, xpath_);
		}
		if (element_ != null && element_.HasAttribute(attrName_))
		{
			string text = element_.GetAttribute(attrName_).Trim();
			if (text.Length > 0)
			{
				try
				{
					result = int.Parse(text);
				}
				catch (Exception)
				{
					throw new Exception($"Expected the \"{attrName_}\" attribute to be an integer.  (Value={text})");
				}
			}
		}
		if (requireValue_ && !result.HasValue)
		{
			string text2 = $"Missing expected parameter, \"{attrName_}\".";
			if (xpath_ != null)
			{
				text2 += $"  (xpath used={xpath_})";
			}
			throw new Exception(text2);
		}
		return result;
	}

	internal static decimal? GetNullableDecimalFromAttribute(XmlElement element_, string attrName_, bool requireValue_ = false, string xpath_ = null)
	{
		decimal? result = null;
		if (element_ != null && xpath_ != null && xpath_.Length > 0)
		{
			element_ = modInternalXMLHelperFunctions.GetChildElementIfThere(element_, xpath_);
		}
		if (element_ != null && element_.HasAttribute(attrName_))
		{
			string text = element_.GetAttribute(attrName_).Trim();
			if (text.Length > 0)
			{
				try
				{
					result = decimal.Parse(text);
				}
				catch (Exception)
				{
					throw new Exception("Expected the \"" + attrName_ + "\" attribute to be an number.  (Value=" + text + ")");
				}
			}
		}
		if (requireValue_ && !result.HasValue)
		{
			string text2 = "Missing expected parameter, \"" + attrName_ + "\".";
			if (xpath_ != null)
			{
				text2 = text2 + "  (xpath used=" + xpath_ + ")";
			}
			throw new Exception(text2);
		}
		return result;
	}

	private XmlDocument ExecuteAndIfNecessaryTraceCommand(string commandDescription_, XmlDocument doc_)
	{
		XmlDocument xmlDocument = null;
		if (CommandTracer != null)
		{
			doc_ = modInternalXMLHelperFunctions.BeautifyXml(doc_);
			try
			{
				CommandTracer.Command(commandDescription_, doc_.OuterXml);
			}
			catch (Exception)
			{
			}
		}
		xmlDocument = ExecuteCommand(doc_, testForErrorResponse_: false, rawUserAgent_: false);
		if (CommandTracer != null)
		{
			try
			{
				CommandTracer.CommandResponse(commandDescription_, modInternalXMLHelperFunctions.BeautifyXmlToText(xmlDocument));
			}
			catch (Exception)
			{
			}
		}
		TestForErrorResponse(xmlDocument);
		return xmlDocument;
	}

	internal static bool AreAllFlagsSet(int flagsToTestFor_, int flagsToTest_)
	{
		return (flagsToTestFor_ & flagsToTest_) == flagsToTestFor_;
	}

	internal static bool AreAnyFlagsSet(int flagsToTestFor_, int flagsToTest_)
	{
		return (flagsToTestFor_ & flagsToTest_) != 0;
	}

	public DisplayOptions GetDisplayOptions()
	{
		ValidateConnected();
		XmlElement xmlElement = CreateCommandDocument("displayOptionsQuery");
		modInternalXMLHelperFunctions.AppendElements(modInternalXMLHelperFunctions.AppendElement(xmlElement, "include"), new string[2] { "currencySymbol", "dateFormat" });
		XmlDocument xmlDocument = ExecuteAndIfNecessaryTraceCommand("Display options query", xmlElement.OwnerDocument);
		return new DisplayOptions(modInternalXMLHelperFunctions.GetTextOfChildIfThere(xmlDocument.DocumentElement, "displayOptionsQuery/currencySymbol"), modInternalXMLHelperFunctions.GetTextOfChildIfThere(xmlDocument.DocumentElement, "displayOptionsQuery/dateFormat"));
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CostList
using Moraware.JobTrackerAPI5;

public class CostList : JTObject
{
	internal enum CostListConditionalFieldUpdateFlags_Enum
	{
		cfufName = 1,
		cfufPostUltimate_CostList
	}

	private string _costListName;

	public int CostListId { get; }

	public string CostListName
	{
		get
		{
			return _costListName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_costListName = value;
		}
	}

	internal bool ModifiedName => base.UpdateFlags.AreFlagsSet(1);

	public int SupplierId { get; private set; }

	public string SupplierName { get; private set; }

	internal CostList(int costListId_)
	{
		CostListId = costListId_;
	}

	internal void SetSupplier(int supplierId_, string supplierName_)
	{
		SupplierId = supplierId_;
		SupplierName = supplierName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CustomFieldFilter
using Moraware.JobTrackerAPI5;

internal class CustomFieldFilter
{
	public int CustomFieldId { get; }

	public ICustomFieldFilter Filter { get; }

	public CustomFieldType.CustomFieldType_Enum CustomFieldType { get; }

	public NumberFilter NumberFilter => (NumberFilter)Filter;

	public TextFilter TextFilter => (TextFilter)Filter;

	public DateFilter DateFilter => (DateFilter)Filter;

	public ListOfValuesFilter ListOfValuesFilter => (ListOfValuesFilter)Filter;

	public CustomFieldFilter(int customFieldId_, ICustomFieldFilter filter_, CustomFieldType.CustomFieldType_Enum customFieldType_)
	{
		Filter = filter_;
		CustomFieldId = customFieldId_;
		CustomFieldType = customFieldType_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CustomFieldFilters
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

internal class CustomFieldFilters : JTObject
{
	internal List<CustomFieldFilter> CustomFieldFiltersList { get; }

	public CustomFieldFilters()
	{
		CustomFieldFiltersList = new List<CustomFieldFilter>();
	}

	public void AddCustomFieldFilter(int customFieldId_, ICustomFieldFilter filter_, CustomFieldType.CustomFieldType_Enum customFieldType_)
	{
		if (filter_ != null)
		{
			CustomFieldFiltersList.Add(new CustomFieldFilter(customFieldId_, filter_, customFieldType_));
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CustomFieldFilterType_Enum
public enum CustomFieldFilterType_Enum
{
	Text = 1,
	Numbers,
	Dates,
	ListOfValues
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CustomFieldType
using Moraware.JobTrackerAPI5;

public abstract class CustomFieldType : JTObject
{
	private enum CustomFieldTypeConditionalFieldUpdateFlags_Enum
	{
		cfufCustomFieldTypeName = 1
	}

	internal enum CustomFieldType_Enum
	{
		Account = 1,
		Job,
		JobActivity,
		File,
		PurchaseOrder,
		Supplier,
		SerialNumber
	}

	public enum CustomFieldDataType_Enum
	{
		Unknown,
		AutoNumber,
		Currency,
		DateField,
		Link,
		ListOfValues,
		MultilineText,
		Number,
		Separator,
		Text
	}

	private string _customFieldTypeName;

	public bool IsInactive { get; }

	public bool IsCustomSort { get; }

	public CustomFieldDataType_Enum CustomFieldDataType { get; }

	public int CustomFieldTypeId { get; }

	public string CustomFieldTypeName
	{
		get
		{
			return _customFieldTypeName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_customFieldTypeName = value;
		}
	}

	internal bool ModifiedCustomFieldTypeName => base.UpdateFlags.AreFlagsSet(1);

	internal static string PrefixFromCustomFieldType(CustomFieldType_Enum customFieldType_)
	{
		return customFieldType_ switch
		{
			CustomFieldType_Enum.Account => "account", 
			CustomFieldType_Enum.File => "file", 
			CustomFieldType_Enum.Job => "job", 
			CustomFieldType_Enum.JobActivity => "jobActivity", 
			CustomFieldType_Enum.PurchaseOrder => "purchaseOrder", 
			CustomFieldType_Enum.SerialNumber => "serialNumber", 
			CustomFieldType_Enum.Supplier => "supplier", 
			_ => throw new APIException("Unknown custom field type:  " + customFieldType_, APIException.APIErrorCodes_Enum.GeneralException), 
		};
	}

	internal static CustomFieldDataType_Enum CustomFieldDataTypeFromDataTypeName(string customFieldDataTypeName_)
	{
		CustomFieldDataType_Enum customFieldDataType_Enum = CustomFieldDataType_Enum.Unknown;
		return customFieldDataTypeName_ switch
		{
			"Auto-number" => CustomFieldDataType_Enum.AutoNumber, 
			"Currency" => CustomFieldDataType_Enum.Currency, 
			"Date" => CustomFieldDataType_Enum.DateField, 
			"Number" => CustomFieldDataType_Enum.Number, 
			"Text" => CustomFieldDataType_Enum.Text, 
			"Link" => CustomFieldDataType_Enum.Link, 
			"Multi-line Text" => CustomFieldDataType_Enum.MultilineText, 
			"List of Values" => CustomFieldDataType_Enum.ListOfValues, 
			"Separator" => CustomFieldDataType_Enum.Separator, 
			_ => CustomFieldDataType_Enum.Unknown, 
		};
	}

	internal CustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
	{
		CustomFieldTypeId = id_;
		_customFieldTypeName = name_;
		IsInactive = isInactive_;
		IsCustomSort = isCustomSort_;
		CustomFieldDataType = CustomFieldDataTypeFromDataTypeName(customFieldDataTypeName_);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CustomFieldValue
using Moraware.JobTrackerAPI5;

public class CustomFieldValue : JTObject
{
	internal enum CustomFieldValueConditionalFieldUpdateFlags_Enum
	{
		cfufFieldValue = 1,
		cfufPostUltimate_CustomFieldValue
	}

	private string _customFieldTypeName;

	private string _fieldValue;

	private int? _fieldValueId;

	private CustomFieldValueContainer _customFieldValueContainer;

	public CustomFieldType.CustomFieldDataType_Enum CustomFieldDataType { get; }

	public string FieldValue
	{
		get
		{
			return _fieldValue;
		}
		set
		{
			_customFieldValueContainer.Modified = true;
			base.UpdateFlags.AddUpdateFlag(1);
			_fieldValue = value;
			_fieldValueId = null;
		}
	}

	public int? FieldValueId
	{
		get
		{
			return _fieldValueId;
		}
		set
		{
			_customFieldValueContainer.Modified = true;
			base.UpdateFlags.AddUpdateFlag(1);
			_fieldValueId = value;
			_fieldValue = null;
		}
	}

	public int CustomFieldTypeId { get; internal set; }

	public string CustomFieldTypeName => _customFieldTypeName;

	internal bool ModifiedFieldValue()
	{
		return base.UpdateFlags.AreFlagsSet(1);
	}

	internal CustomFieldValue(CustomFieldValueContainer customFieldValueContainer_, int id_, string name_, string customFieldDataTypeName_)
	{
		CustomFieldTypeId = id_;
		_customFieldTypeName = name_;
		_customFieldValueContainer = customFieldValueContainer_;
		CustomFieldDataType = CustomFieldType.CustomFieldDataTypeFromDataTypeName(customFieldDataTypeName_);
	}

	internal void SetFieldIdAndValue(int? fieldValueId_, string fieldValue_)
	{
		_customFieldValueContainer.Modified = true;
		base.UpdateFlags.AddUpdateFlag(1);
		_fieldValue = fieldValue_;
		_fieldValueId = fieldValueId_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CustomFieldValueContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class CustomFieldValueContainer : IEnumerable<CustomFieldValue>, IEnumerable
{
	private Dictionary<int, CustomFieldValue> _mapById;

	private List<CustomFieldValue> _list = new List<CustomFieldValue>();

	internal bool Modified { get; set; }

	internal Dictionary<int, CustomFieldValue> MapById
	{
		get
		{
			if (_mapById == null)
			{
				_mapById = new Dictionary<int, CustomFieldValue>();
				foreach (CustomFieldValue item in _list)
				{
					_mapById.Add(item.CustomFieldTypeId, item);
				}
			}
			return _mapById;
		}
	}

	internal void Clear()
	{
		_list.Clear();
		if (_mapById != null)
		{
			_mapById = null;
		}
	}

	internal void ClearUpdateFlags()
	{
		Modified = false;
		using IEnumerator<CustomFieldValue> enumerator = GetEnumerator();
		while (enumerator.MoveNext())
		{
			enumerator.Current.ClearUpdateFlags();
		}
	}

	public CustomFieldValue ItemAt(int zeroBasedIndex_)
	{
		return _list[zeroBasedIndex_];
	}

	public CustomFieldValue Item(int customFieldTypeId_)
	{
		CustomFieldValue customFieldValue = null;
		if (MapById.ContainsKey(customFieldTypeId_))
		{
			return MapById[customFieldTypeId_];
		}
		return null;
	}

	public CustomFieldValue Item(string customFieldName_, bool exceptionIfNotThere_ = false)
	{
		CustomFieldValue customFieldValue = null;
		using (IEnumerator<CustomFieldValue> enumerator = GetEnumerator())
		{
			while (enumerator.MoveNext())
			{
				CustomFieldValue current = enumerator.Current;
				if (customFieldName_ == current.CustomFieldTypeName)
				{
					return current;
				}
			}
		}
		if (exceptionIfNotThere_)
		{
			throw new APIException(null, "No such item (name=\"" + customFieldName_ + "\").", APIException.APIErrorCodes_Enum.NonExistentObject);
		}
		return null;
	}

	internal CustomFieldValue Add(CustomFieldValue t_)
	{
		if (_mapById != null)
		{
			_mapById.Add(t_.CustomFieldTypeId, t_);
		}
		_list.Add(t_);
		Modified = true;
		return t_;
	}

	public bool ContainsItemWithId(int id_)
	{
		return MapById.ContainsKey(id_);
	}

	public int Count()
	{
		return _list.Count;
	}

	public IEnumerator<CustomFieldValue> GetEnumerator()
	{
		return _list.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}

	internal CustomFieldValue AddCustomFieldValue(int customFieldTypeId_, string customFieldTypeName_, string customFieldDataTypeName_)
	{
		CustomFieldValue t_ = new CustomFieldValue(this, customFieldTypeId_, customFieldTypeName_, customFieldDataTypeName_);
		return Add(t_);
	}

	public void SetFieldValue(int customFieldTypeId_, string fieldValue_)
	{
		CustomFieldValue customFieldValue = null;
		if (ContainsItemWithId(customFieldTypeId_))
		{
			customFieldValue = Item(customFieldTypeId_);
		}
		else
		{
			customFieldValue = new CustomFieldValue(this, customFieldTypeId_, null, null);
			customFieldValue = Add(customFieldValue);
		}
		customFieldValue.FieldValue = fieldValue_;
	}

	public void SetFieldValueId(int customFieldTypeId_, int? fieldValueId_)
	{
		CustomFieldValue customFieldValue = null;
		if (ContainsItemWithId(customFieldTypeId_))
		{
			customFieldValue = Item(customFieldTypeId_);
		}
		else
		{
			customFieldValue = new CustomFieldValue(this, customFieldTypeId_, null, null);
			customFieldValue = Add(customFieldValue);
		}
		customFieldValue.FieldValueId = fieldValueId_;
	}

	public string GetFieldValue(int customFieldTypeId_)
	{
		CustomFieldValue customFieldValue = Item(customFieldTypeId_);
		if (customFieldValue == null)
		{
			return "";
		}
		return customFieldValue.FieldValue;
	}

	public string GetFieldValue(string customFieldName_)
	{
		CustomFieldValue customFieldValue = Item(customFieldName_);
		if (customFieldValue == null)
		{
			return "";
		}
		return customFieldValue.FieldValue;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.CustomLOVFieldValue
public class CustomLOVFieldValue
{
	public int Id { get; }

	public string Value { get; }

	public bool IsInactive { get; }

	public string DisplayColor { get; }

	public int? SeqNum { get; }

	internal CustomLOVFieldValue(int id_, string value_, bool isInactive_, string displayColor_, int? seqNum_)
	{
		Id = id_;
		Value = value_;
		IsInactive = isInactive_;
		DisplayColor = displayColor_;
		SeqNum = seqNum_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.DateFilter
using System;
using Moraware.JobTrackerAPI5;

public class DateFilter : Filter, ICustomFieldFilter, IFilter, ICloneable
{
	private bool _empty;

	private int? _atLeastDaysAgo;

	private int? _atLeastDaysFromToday;

	private DateTime? _atLeastDate;

	private int? _atMostDaysAgo;

	private int? _atMostDaysFromToday;

	private DateTime? _atMostDate;

	public DateTime? AtLeastDate
	{
		get
		{
			return _atLeastDate;
		}
		set
		{
			_atLeastDate = value;
			if (value.HasValue)
			{
				_empty = false;
				_atLeastDaysAgo = null;
				_atLeastDaysFromToday = null;
			}
		}
	}

	public int? AtLeastDaysAgo
	{
		get
		{
			return _atLeastDaysAgo;
		}
		set
		{
			_atLeastDaysAgo = value;
			if (value.HasValue)
			{
				_empty = false;
				_atLeastDate = null;
				_atLeastDaysFromToday = null;
			}
		}
	}

	public int? AtLeastDaysFromToday
	{
		get
		{
			return _atLeastDaysFromToday;
		}
		set
		{
			_atLeastDaysFromToday = value;
			if (value.HasValue)
			{
				_empty = false;
				_atLeastDate = null;
				_atLeastDaysAgo = null;
			}
		}
	}

	public int? AtMostDaysAgo
	{
		get
		{
			return _atMostDaysAgo;
		}
		set
		{
			_atMostDaysAgo = value;
			if (value.HasValue)
			{
				_empty = false;
				_atMostDate = null;
				_atMostDaysFromToday = null;
			}
		}
	}

	public int? AtMostDaysFromToday
	{
		get
		{
			return _atMostDaysFromToday;
		}
		set
		{
			_atMostDaysFromToday = value;
			if (value.HasValue)
			{
				_empty = false;
				_atMostDate = null;
				_atMostDaysFromToday = null;
			}
		}
	}

	public DateTime? AtMostDate
	{
		get
		{
			return _atMostDate;
		}
		set
		{
			_atMostDate = value;
			if (value.HasValue)
			{
				_empty = false;
				_atMostDaysAgo = null;
				_atMostDaysFromToday = null;
			}
		}
	}

	public bool Empty
	{
		get
		{
			return _empty;
		}
		set
		{
			_empty = value;
			if (value)
			{
				_atLeastDate = null;
				_atLeastDaysAgo = null;
				_atLeastDaysFromToday = null;
				_atMostDate = null;
				_atMostDaysAgo = null;
				_atMostDaysFromToday = null;
			}
		}
	}

	public CustomFieldFilterType_Enum FilterType => CustomFieldFilterType_Enum.Dates;

	private DateFilter(bool empty_, int? atLeastDaysAgo_, int? atLeastDaysFromToday_, DateTime? atLeastDate_, int? atMostDaysAgo_, int? atMostDaysFromToday_, DateTime? atMostDate_)
	{
		_empty = empty_;
		_atLeastDate = atLeastDate_;
		_atLeastDaysAgo = atLeastDaysAgo_;
		_atLeastDaysFromToday = atLeastDaysFromToday_;
		_atMostDate = atMostDate_;
		_atMostDaysAgo = atMostDaysAgo_;
		_atMostDaysFromToday = atMostDaysFromToday_;
	}

	public DateFilter(bool empty_)
		: this(empty_, null, null, null, null, null, null)
	{
	}

	public DateFilter(DateTime? atLeastDate_, DateTime? atMostDate_)
		: this(empty_: false, null, null, atLeastDate_, null, null, atMostDate_)
	{
	}

	public DateFilter(int? atLeastDays_, bool atLeastDaysAgo_, int? atMostDays_, bool atMostDaysAgo_)
		: this(empty_: false, atLeastDaysAgo_ ? atLeastDays_ : ((int?)null), atLeastDaysAgo_ ? ((int?)null) : atLeastDays_, null, atMostDaysAgo_ ? atMostDays_ : ((int?)null), atMostDaysAgo_ ? ((int?)null) : atMostDays_, null)
	{
	}

	public DateFilter(DateTime? atLeastDate_, int? atMostDays_, bool atMostDaysAgo_)
		: this(empty_: false, null, null, atLeastDate_, atMostDaysAgo_ ? atMostDays_ : ((int?)null), atMostDaysAgo_ ? ((int?)null) : atMostDays_, null)
	{
	}

	public DateFilter(int? atLeastDays_, bool atLeastDaysAgo_, DateTime? atMostDate_)
		: this(empty_: false, atLeastDaysAgo_ ? atLeastDays_ : ((int?)null), atLeastDaysAgo_ ? ((int?)null) : atLeastDays_, null, null, null, atMostDate_)
	{
	}

	public string BuildDescription(string fieldName_, string dateFormat_)
	{
		string text = fieldName_;
		if (Empty)
		{
			text += " is empty";
		}
		else if (AtLeastDate.HasValue || AtLeastDaysAgo.HasValue || AtLeastDaysFromToday.HasValue || AtMostDate.HasValue || AtMostDaysAgo.HasValue || AtMostDaysFromToday.HasValue)
		{
			text += " occurs";
			if (AtLeastDate.HasValue)
			{
				text += $" no earlier than {AtLeastDate.Value.ToString(dateFormat_)}";
			}
			else if (AtLeastDaysAgo.HasValue)
			{
				text += $" no earlier than {AtLeastDaysAgo} days ago";
			}
			else if (AtLeastDaysFromToday.HasValue)
			{
				text += $" no earlier than {AtLeastDaysFromToday} days from today";
			}
			if ((AtLeastDate.HasValue || AtLeastDaysAgo.HasValue || AtLeastDaysFromToday.HasValue) & (AtMostDate.HasValue || AtMostDaysAgo.HasValue || AtMostDaysFromToday.HasValue))
			{
				text += " and ";
			}
			if (AtMostDate.HasValue)
			{
				text += $" no later than {AtMostDate.Value.ToString(dateFormat_)}";
			}
			else if (AtMostDaysAgo.HasValue)
			{
				text += $" no later than {AtMostDaysAgo} days ago";
			}
			else if (AtMostDaysFromToday.HasValue)
			{
				text += $" no later than {AtMostDaysFromToday} days from today";
			}
		}
		else
		{
			text += " is any date";
		}
		return text;
	}

	public override object Clone()
	{
		return new DateFilter(Empty, AtLeastDaysAgo, AtLeastDaysFromToday, AtLeastDate, AtMostDaysAgo, AtMostDaysFromToday, AtMostDate);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.DefaultJobTemplate
using Moraware.JobTrackerAPI5;

internal class DefaultJobTemplate
{
	internal bool Modified { get; set; }

	public int ProcessId { get; }

	public JobTemplate JobTemplate { get; }

	internal DefaultJobTemplate(int processId_, JobTemplate jobTemplate_)
	{
		ProcessId = processId_;
		JobTemplate = jobTemplate_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.DefaultJobTemplateContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

internal class DefaultJobTemplateContainer : IEnumerable<DefaultJobTemplate>, IEnumerable
{
	private Dictionary<int, DefaultJobTemplate> _defaultJobTemplates = new Dictionary<int, DefaultJobTemplate>();

	internal void ClearUpdateFlags()
	{
		using IEnumerator<DefaultJobTemplate> enumerator = GetEnumerator();
		while (enumerator.MoveNext())
		{
			enumerator.Current.Modified = false;
		}
	}

	public IEnumerator<DefaultJobTemplate> GetEnumerator()
	{
		return _defaultJobTemplates.Values.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator1();
	}

	public IEnumerator GetEnumerator1()
	{
		return _defaultJobTemplates.Values.GetEnumerator();
	}

	public JobTemplate GetJobTemplate(int processId_)
	{
		if (_defaultJobTemplates.ContainsKey(processId_))
		{
			return _defaultJobTemplates[processId_].JobTemplate;
		}
		return null;
	}

	public void SetJobTemplate(int processId_, JobTemplate value)
	{
		DefaultJobTemplate value2 = new DefaultJobTemplate(processId_, value)
		{
			Modified = true
		};
		_defaultJobTemplates[processId_] = value2;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.DisplayOptions
public class DisplayOptions
{
	public string CurrencySymbol { get; }

	public string DateFormat { get; }

	internal DisplayOptions(string currencySymbol_, string dateFormat_)
	{
		CurrencySymbol = currencySymbol_;
		DateFormat = dateFormat_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.FileCustomFieldType
using Moraware.JobTrackerAPI5;

public class FileCustomFieldType : CustomFieldType
{
	internal FileCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.FileTransferProgressEvent
using System;
using Moraware.JobTrackerAPI5;

public class FileTransferProgressEvent
{
	public enum FileTransferEventProgressStatus_Enum
	{
		TransferInProgress,
		CompletedWithException,
		CompletedSuccessfully,
		Cancelled
	}

	public int ExpectedBytes { get; internal set; }

	public int BytesSoFar { get; internal set; }

	public FileTransferEventProgressStatus_Enum Status { get; private set; }

	public Exception ExceptionObject { get; }

	public bool Halted { get; private set; }

	internal FileTransferProgressEvent(int bytesSoFar_, int expectedBytes_)
	{
		BytesSoFar = bytesSoFar_;
		ExpectedBytes = expectedBytes_;
	}

	internal FileTransferProgressEvent(int bytesSoFar_, int expectedBytes_, bool cancelled_)
		: this(bytesSoFar_, expectedBytes_)
	{
		if (cancelled_)
		{
			Status = FileTransferEventProgressStatus_Enum.Cancelled;
		}
	}

	internal FileTransferProgressEvent(int bytesSoFar_, int expectedBytes_, Exception exception_)
		: this(bytesSoFar_, expectedBytes_)
	{
		ExceptionObject = exception_;
		Status = FileTransferEventProgressStatus_Enum.CompletedWithException;
	}

	internal FileTransferProgressEvent(int totalBytes_)
		: this(totalBytes_, totalBytes_)
	{
		Status = FileTransferEventProgressStatus_Enum.CompletedSuccessfully;
	}

	public void Halt()
	{
		Halted = true;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Filter
using System;
using Moraware.JobTrackerAPI5;

public abstract class Filter : IFilter, ICloneable
{
	public abstract object Clone();
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.FormTemplate
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class FormTemplate : JTObject
{
	private List<int> _processes;

	public bool IsInactive { get; set; }

	public List<FormTemplateField> FormFields { get; set; }

	public int FormTemplateId { get; }

	public string FormTemplateName { get; }

	public IEnumerable<int> Processes => _processes;

	internal FormTemplate(int id_, string name_, bool isInactive_, IEnumerable<int> processes_)
	{
		FormTemplateId = id_;
		FormTemplateName = name_;
		IsInactive = isInactive_;
		_processes = new List<int>();
		if (processes_ != null)
		{
			_processes.AddRange(processes_);
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.FormTemplateField
using Moraware.JobTrackerAPI5;

public class FormTemplateField : JTObject
{
	public enum FormFieldDataType_Enum
	{
		Unknown,
		AutoNumber,
		CheckBox,
		Currency,
		DateField,
		Link,
		SelectFromList,
		MultilineText,
		Number,
		Text,
		Separator
	}

	public bool IsCustomSort { get; }

	public bool IsInactive { get; }

	public FormFieldDataType_Enum FormFieldDataType { get; }

	public int FormTemplateFieldId { get; }

	public string FormTemplateFieldName { get; }

	internal static FormFieldDataType_Enum FormFieldDataTypeFromFormFieldDataTypeName(string formFieldDataTypeName_)
	{
		FormFieldDataType_Enum formFieldDataType_Enum = FormFieldDataType_Enum.Unknown;
		return formFieldDataTypeName_ switch
		{
			"Auto-number" => FormFieldDataType_Enum.AutoNumber, 
			"Checkbox" => FormFieldDataType_Enum.CheckBox, 
			"Currency" => FormFieldDataType_Enum.Currency, 
			"Date" => FormFieldDataType_Enum.DateField, 
			"Link" => FormFieldDataType_Enum.Link, 
			"List of Values" => FormFieldDataType_Enum.SelectFromList, 
			"Multi-line Text" => FormFieldDataType_Enum.MultilineText, 
			"Number" => FormFieldDataType_Enum.Number, 
			"Text" => FormFieldDataType_Enum.Text, 
			"Separator" => FormFieldDataType_Enum.Separator, 
			_ => FormFieldDataType_Enum.Unknown, 
		};
	}

	internal FormTemplateField(int id_, string name_, bool isCustomSort_, string formFieldDataTypeName_, bool isInactive_)
	{
		FormTemplateFieldId = id_;
		FormTemplateFieldName = name_;
		IsCustomSort = isCustomSort_;
		IsInactive = isInactive_;
		FormFieldDataType = FormFieldDataTypeFromFormFieldDataTypeName(formFieldDataTypeName_);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.FormTemplateLOVFieldValue
public class FormTemplateLOVFieldValue
{
	public int Id { get; }

	public string Value { get; }

	public bool IsInactive { get; }

	public string DisplayColor { get; }

	public int? SeqNum { get; }

	internal FormTemplateLOVFieldValue(int id_, string value_, bool isInactive_, string displayColor_, int? seqNum_)
	{
		Id = id_;
		Value = value_;
		IsInactive = isInactive_;
		DisplayColor = displayColor_;
		SeqNum = seqNum_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.GenericListOfValuesFilter<V,L>
using System;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

internal class GenericListOfValuesFilter<V, L> : Filter where L : IGenericListOfValuesFilterValues<V>, ICloneable, new()
{
	public bool Invert { get; set; }

	public L Values { get; }

	public GenericListOfValuesFilter(bool invert_, L values_)
	{
		Invert = invert_;
		if (values_ == null)
		{
			values_ = new L();
		}
		Values = values_;
	}

	public string BuildDescription(string fieldName_, Dictionary<V, string> lovValues_)
	{
		string text = "";
		if (Values.DoIncludeNone())
		{
			text = "[None]";
		}
		if (Values.Values.Count > 0)
		{
			foreach (V value in Values.Values)
			{
				if (text.Length > 0)
				{
					text += ",";
				}
				string text2 = null;
				text2 = ((!lovValues_.ContainsKey(value)) ? ("[id=" + value.ToString() + "]") : lovValues_[value]);
				text = text + "\"" + text2 + "\"";
			}
		}
		return fieldName_ + " is" + (Invert ? " not" : "") + " one of {" + text + "}";
	}

	public override object Clone()
	{
		return new GenericListOfValuesFilter<V, L>(Invert, (L)Values.Clone());
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.GenericListOfValuesFilterValues<V>
using System;
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

internal class GenericListOfValuesFilterValues<V> : IEnumerable<V>, IEnumerable, IGenericListOfValuesFilterValues<V>, ICloneable
{
	internal List<V> Values { get; } = new List<V>();

	List<V> IGenericListOfValuesFilterValues<V>.Values => Values;

	public GenericListOfValuesFilterValues()
	{
	}

	public GenericListOfValuesFilterValues(IEnumerable<V> values_)
	{
		if (values_ == null)
		{
			return;
		}
		foreach (V item in values_)
		{
			Values.Add(item);
		}
	}

	public virtual object Clone()
	{
		return new GenericListOfValuesFilterValues<V>(Values);
	}

	public IEnumerator<V> GetEnumerator()
	{
		return Values.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator1();
	}

	public IEnumerator GetEnumerator1()
	{
		return Values.GetEnumerator();
	}

	internal virtual bool DoIncludeNone()
	{
		return false;
	}

	bool IGenericListOfValuesFilterValues<V>.DoIncludeNone()
	{
		return DoIncludeNone();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.GenericNullableListOfValuesFilterValues<V>
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

internal class GenericNullableListOfValuesFilterValues<V> : GenericListOfValuesFilterValues<V>
{
	public bool IncludeNone { get; set; }

	public GenericNullableListOfValuesFilterValues(bool includeNone_)
		: this(includeNone_, (IEnumerable<V>)null)
	{
	}

	public GenericNullableListOfValuesFilterValues(bool includeNone_, IEnumerable<V> values_)
		: base(values_)
	{
		IncludeNone = includeNone_;
	}

	public GenericNullableListOfValuesFilterValues(IEnumerable<V> values_)
		: base(values_)
	{
		IncludeNone = false;
	}

	public override object Clone()
	{
		return new GenericNullableListOfValuesFilterValues<V>(IncludeNone, base.Values);
	}

	internal override bool DoIncludeNone()
	{
		return IncludeNone;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.HasCustomFieldValues
using Moraware.JobTrackerAPI5;

public class HasCustomFieldValues : JTObject
{
	private CustomFieldValueContainer _customFieldValues;

	public CustomFieldValueContainer CustomFieldValues
	{
		get
		{
			if (_customFieldValues == null)
			{
				_customFieldValues = new CustomFieldValueContainer();
			}
			return _customFieldValues;
		}
		internal set
		{
			_customFieldValues = value;
		}
	}

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (_customFieldValues != null)
		{
			_customFieldValues.ClearUpdateFlags();
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ICustomFieldFilter
using System;
using Moraware.JobTrackerAPI5;

public interface ICustomFieldFilter : IFilter, ICloneable
{
	CustomFieldFilterType_Enum FilterType { get; }
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.IFileTransferMonitor
using Moraware.JobTrackerAPI5;

public interface IFileTransferMonitor
{
	void UpdateStatus(FileTransferProgressEvent event_);
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.IFilter
using System;

public interface IFilter : ICloneable
{
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.IGenericListOfValuesFilterValues<V>
using System;
using System.Collections;
using System.Collections.Generic;

internal interface IGenericListOfValuesFilterValues<V> : IEnumerable<V>, IEnumerable, ICloneable
{
	List<V> Values { get; }

	bool DoIncludeNone();
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.InventoryCount
using System;
using Moraware.JobTrackerAPI5;

public class InventoryCount : JTObject
{
	internal enum InventoryCountConditionalFieldUpdateFlags_Enum
	{
		cfufName = 1,
		cfufFrozen = 2,
		cfufPostUltimate_InventoryCount = 4
	}

	private int m_inventoryCountId;

	private string m_inventoryCountName;

	private DateTime? m_frozenTimestamp;

	private string m_frozenBy;

	private bool m_frozen;

	public int InventoryCountId => m_inventoryCountId;

	public string InventoryCountName
	{
		get
		{
			return m_inventoryCountName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			m_inventoryCountName = value;
		}
	}

	internal bool ModifiedName => base.UpdateFlags.AreFlagsSet(1);

	public DateTime? FrozenTimestamp => m_frozenTimestamp;

	public string FrozenBy => m_frozenBy;

	public bool Frozen
	{
		get
		{
			return m_frozen;
		}
		set
		{
			m_frozen = value;
			base.UpdateFlags.AddUpdateFlag(2);
			m_frozenBy = null;
			m_frozenTimestamp = null;
		}
	}

	internal bool ModifiedFrozen => base.UpdateFlags.AreFlagsSet(2);

	internal InventoryCount(int inventoryCountId_, string inventoryCountName_, DateTime? frozenTimestamp_, string frozenBy_)
	{
		m_frozen = frozenTimestamp_.HasValue;
		m_frozenBy = frozenBy_;
		m_frozenTimestamp = frozenTimestamp_;
		m_inventoryCountId = inventoryCountId_;
		m_inventoryCountName = inventoryCountName_;
	}

	public InventoryCount(string inventoryCountName_)
		: this(0, inventoryCountName_, null, null)
	{
	}

	public InventoryCount(int inventoryCountId_)
	{
		m_inventoryCountId = inventoryCountId_;
	}

	internal void SetInventoryCountId(int id_)
	{
		m_inventoryCountId = id_;
	}

	internal void SetFrozen(DateTime? frozenTimestamp_, string frozenBy_)
	{
		m_frozenTimestamp = frozenTimestamp_;
		m_frozenBy = frozenBy_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.InventoryCountDetail
using System;
using Moraware.JobTrackerAPI5;

public class InventoryCountDetail : JTObject
{
	internal enum InventoryCountDetailConditionalFieldUpdateFlags_Enum
	{
		cfufLocation = 1,
		cfufCountType = 2,
		cfufQuantity = 4,
		cfufPostUltimate_InventoryCountDetail = 8
	}

	public enum IdType_Enum
	{
		PurchaseProductVariant_IdType = 1,
		SerialNumber_IdType
	}

	private Guid? _id;

	private string _location;

	public string Location
	{
		get
		{
			return _location;
		}
		set
		{
			_location = value;
			base.UpdateFlags.AddUpdateFlag(1);
		}
	}

	public string CountType { get; internal set; }

	public decimal Quantity { get; internal set; }

	public int PurchaseProductVariantId { get; internal set; }

	public string PurchaseProductVariantName { get; internal set; }

	public int PurchaseProductId { get; internal set; }

	public string PurchaseProductName { get; internal set; }

	public string CountedBy { get; internal set; }

	public DateTime CountTimestamp { get; internal set; }

	public Guid Id
	{
		get
		{
			Guid guid = default(Guid);
			return _id ?? guid;
		}
		internal set
		{
			_id = value;
		}
	}

	public string SerialNumberName { get; internal set; }

	public int? SerialNumberId { get; internal set; }

	public int InventoryCountId { get; }

	internal IdType_Enum? IdTypeOnCreate { get; }

	internal InventoryCountDetail()
	{
	}

	public InventoryCountDetail(int inventoryCountId_, string serialNumberName_, decimal quantity_, string countType_)
	{
		InventoryCountId = inventoryCountId_;
		Quantity = quantity_;
		CountType = countType_;
		SerialNumberName = serialNumberName_;
	}

	public InventoryCountDetail(int inventoryCountId_, int id_, IdType_Enum idType_, decimal quantity_, string countType_)
	{
		InventoryCountId = inventoryCountId_;
		Quantity = quantity_;
		CountType = countType_;
		switch (idType_)
		{
		case IdType_Enum.PurchaseProductVariant_IdType:
			PurchaseProductVariantId = id_;
			break;
		case IdType_Enum.SerialNumber_IdType:
			SerialNumberId = id_;
			break;
		default:
			throw new Exception($"Invalid IdType={idType_}");
		}
		IdTypeOnCreate = idType_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.InventoryLocation
using Moraware.JobTrackerAPI5;

public class InventoryLocation : JTObject
{
	internal enum InventoryLocationConditionalFieldUpdateFlags_Enum
	{
		cfufInventoryLocationName = 1,
		cfufIsInactive = 2,
		cfufPostUltimate_InventoryLocation = 4
	}

	private string _inventoryLocationName;

	private bool _isInactive;

	internal bool ModifiedIsInactive => base.UpdateFlags.AreFlagsSet(2);

	public bool IsInactive
	{
		get
		{
			return _isInactive;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_isInactive = value;
		}
	}

	public int InventoryLocationId { get; internal set; }

	public string InventoryLocationName
	{
		get
		{
			return _inventoryLocationName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_inventoryLocationName = value;
		}
	}

	internal bool ModifiedInventoryLocationName => base.UpdateFlags.AreFlagsSet(1);

	public InventoryLocation(int inventoryLocationId_)
	{
		InventoryLocationId = inventoryLocationId_;
	}

	public InventoryLocation(string inventoryLocationName_)
	{
		InventoryLocationName = inventoryLocationName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Job
using System;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class Job : HasCustomFieldValues
{
	internal enum JobConditionalFieldUpdateFlags_Enum
	{
		cfufJobName = 1,
		cfufCreationDate = 2,
		cfufSalesperson = 4,
		cfufAddress = 8,
		cfufNotes = 0x10,
		cfufPostUltimate_Job = 0x20
	}

	public enum JobStatus_Enum
	{
		jsActive = 1,
		jsComplete
	}

	private string _processName;

	private string _jobName;

	private DateTime _creationDate;

	private string _salespersonName;

	private int? _salespersonId;

	private Address _address;

	private string _notes;

	internal bool ModifiedCreationDate => base.UpdateFlags.AreFlagsSet(2);

	internal bool ModifiedAddress
	{
		get
		{
			if (base.UpdateFlags.AreFlagsSet(8))
			{
				return true;
			}
			if (Address == null)
			{
				return false;
			}
			return Address.Modified;
		}
	}

	internal bool ModifiedNotes => base.UpdateFlags.AreFlagsSet(16);

	internal bool ModifiedSalesperson => base.UpdateFlags.AreFlagsSet(4);

	public string SalespersonName
	{
		get
		{
			return _salespersonName;
		}
		set
		{
			SetSalesperson(null, value);
		}
	}

	public int? SalespersonId
	{
		get
		{
			return _salespersonId;
		}
		set
		{
			SetSalesperson(value, null);
		}
	}

	public DateTime CreationDate
	{
		get
		{
			return _creationDate;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_creationDate = value;
		}
	}

	public Address Address
	{
		get
		{
			return _address;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			_address = value;
		}
	}

	public int AccountId { get; internal set; }

	public string AccountName { get; internal set; } = "";

	public string Notes
	{
		get
		{
			return _notes;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(16);
			_notes = value;
		}
	}

	public JobContactContainer Contacts { get; } = new JobContactContainer();

	public List<JobPhase> JobPhases { get; set; }

	public int JobId { get; internal set; }

	public string JobName
	{
		get
		{
			return _jobName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_jobName = value;
		}
	}

	internal bool ModifiedJobName => base.UpdateFlags.AreFlagsSet(1);

	public int ProcessId { get; internal set; }

	public string ProcessName => _processName;

	internal bool IsComplete { private get; set; }

	public JobStatus_Enum JobStatus
	{
		get
		{
			if (!IsComplete)
			{
				return JobStatus_Enum.jsActive;
			}
			return JobStatus_Enum.jsComplete;
		}
	}

	private Job()
	{
	}

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (Address != null)
		{
			Address.ClearUpdateFlags();
		}
		if (Contacts != null)
		{
			Contacts.ClearUpdateFlags();
		}
	}

	public Job(int jobId_)
	{
		JobId = jobId_;
	}

	public Job(int accountId_, string jobName_, int processId_)
	{
		AccountId = accountId_;
		JobName = jobName_;
		ProcessId = processId_;
	}

	internal void SetSalesperson(int? salespersonId_, string salespersonName_)
	{
		base.UpdateFlags.AddUpdateFlag(4);
		_salespersonId = salespersonId_;
		_salespersonName = salespersonName_;
	}

	internal void SetProcessName(string processName_)
	{
		_processName = processName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobActivity
using System;
using Moraware.JobTrackerAPI5;

public class JobActivity : HasCustomFieldValues
{
	internal enum JobActivityConditionalFieldUpdateFlags_Enum
	{
		cfufStartDate = 1,
		cfufScheduledDuration = 2,
		cfufScheduledTime = 4,
		cfufJobActivityStatus = 8,
		cfufNotes = 0x10,
		cfufAssignees = 0x20,
		cfufPostUltimate_JobActivity = 0x40
	}

	private int _jobActivityStatusId;

	private DateTime? _startDate;

	private DateTime? _scheduledDuration;

	private DateTime? _scheduledTime;

	private string _notes;

	private AssigneeContainer _assignees = new AssigneeContainer();

	internal bool ModifiedAssignees
	{
		get
		{
			if (base.UpdateFlags.AreFlagsSet(32))
			{
				return true;
			}
			if (Assignees == null)
			{
				return false;
			}
			return Assignees.Modified;
		}
	}

	internal bool ModifiedJobActivityStatus => base.UpdateFlags.AreFlagsSet(8);

	internal bool ModifiedNotes => base.UpdateFlags.AreFlagsSet(16);

	internal bool ModifiedScheduledDuration => base.UpdateFlags.AreFlagsSet(2);

	internal bool ModifiedScheduledTime => base.UpdateFlags.AreFlagsSet(4);

	internal bool ModifiedStartDate => base.UpdateFlags.AreFlagsSet(1);

	public int JobActivityStatusId
	{
		get
		{
			return _jobActivityStatusId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			_jobActivityStatusId = value;
		}
	}

	public string JobActivityStatusName { get; private set; }

	public DateTime? StartDate
	{
		get
		{
			return _startDate;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_startDate = value;
		}
	}

	public int JobActivityTypeId { get; internal set; }

	public AssigneeContainer Assignees
	{
		get
		{
			return _assignees;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(32);
			_assignees = value;
		}
	}

	public DateTime? ScheduledTime
	{
		get
		{
			return _scheduledTime;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_scheduledTime = value;
		}
	}

	public DateTime? ScheduledDuration
	{
		get
		{
			return _scheduledDuration;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_scheduledDuration = value;
		}
	}

	public string Notes
	{
		get
		{
			return _notes;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(16);
			_notes = value;
		}
	}

	public JobPhaseContainer JobPhases { get; } = new JobPhaseContainer();

	public JobActivitySeriesMember JobActivitySeriesMember { get; internal set; }

	public int JobId { get; internal set; }

	public int JobActivityId { get; internal set; }

	public string JobActivityTypeName { get; internal set; }

	public JobActivity(int jobActivityId_)
	{
		JobActivityId = jobActivityId_;
	}

	public JobActivity(int jobId_, int jobActivityTypeId_, int jobActivityStatusId_)
	{
		JobId = jobId_;
		JobActivityTypeId = jobActivityTypeId_;
		JobActivityStatusId = jobActivityStatusId_;
	}

	internal void SetJobActivityStatusIdAndName(int jobActivityStatusId_, string jobActivityStatusName_)
	{
		_jobActivityStatusId = jobActivityStatusId_;
		JobActivityStatusName = jobActivityStatusName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobActivityCustomFieldType
using Moraware.JobTrackerAPI5;

public class JobActivityCustomFieldType : CustomFieldType
{
	internal JobActivityCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobActivityMaterial
using Moraware.JobTrackerAPI5;

public class JobActivityMaterial : JTObject
{
	internal enum JobActivityMaterialConditionalFieldUpdateFlags_Enum
	{
		cfufOrderedQuantity = 1,
		cfufUnitCost = 2,
		cfufIsTaxable = 4,
		cfufPostUltimate_PurchaseOrder = 8
	}

	public SerialNumberAllocationContainer SerialNumberAllocations { get; } = new SerialNumberAllocationContainer();

	internal bool ModifiedSerialNumberAllocations => SerialNumberAllocations.Modified;

	public PurchaseProductVariantAllocation PurchaseProductVariantAllocation { get; }

	public int PurchaseProductVariantId => PurchaseProductVariantAllocation.PurchaseProductVariantId;

	public string PurchaseProductVariantName => PurchaseProductVariantAllocation.PurchaseProductVariantName;

	public int JobId => PurchaseProductVariantAllocation.JobId;

	public string JobName => PurchaseProductVariantAllocation.JobName;

	public int JobActivityId => PurchaseProductVariantAllocation.JobActivityId;

	public int JobActivityTypeId => PurchaseProductVariantAllocation.JobActivityTypeId;

	public string JobActivityTypeName => PurchaseProductVariantAllocation.JobActivityTypeName;

	internal PurchaseProductVariant PurchaseProductVariantForCreate
	{
		get
		{
			return PurchaseProductVariantAllocation.PurchaseProductVariantForCreate;
		}
		set
		{
			PurchaseProductVariantAllocation.PurchaseProductVariantForCreate = value;
		}
	}

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		SerialNumberAllocations.ClearUpdateFlags();
		PurchaseProductVariantAllocation.ClearUpdateFlags();
	}

	public JobActivityMaterial(int jobActivityId_, int purchaseProductVariantId_)
		: this(null, purchaseProductVariantId_, null, 0, null, jobActivityId_, 0, null, 0m)
	{
	}

	public JobActivityMaterial(int jobActivityId_, PurchaseProductVariant purchaseProductVariant_)
		: this(purchaseProductVariant_, 0, null, 0, null, jobActivityId_, 0, null, 0m)
	{
	}

	internal JobActivityMaterial(PurchaseProductVariant ppvForCreate_, int pvId_, string pvName_, int jobId_, string jobName_, int jaId_, int atId_, string atName_, decimal unserializedQuantity_)
	{
		PurchaseProductVariantAllocation = new PurchaseProductVariantAllocation(ppvForCreate_, pvId_, pvName_, jobId_, jobName_, jaId_, atId_, atName_, unserializedQuantity_);
		ClearUpdateFlags();
	}

	public void AddSerialNumberAllocation(string serialNumberName_, decimal quantity_)
	{
		SerialNumberAllocations.AddAllocation(new SerialNumberAllocation(JobActivityId, serialNumberName_, quantity_));
	}

	public void AddSerialNumberAllocation(int serialNumberId_, decimal quantity_)
	{
		SerialNumberAllocations.AddAllocation(new SerialNumberAllocation(JobActivityId, serialNumberId_, quantity_));
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobActivitySeries
using System;
using System.Text;
using Moraware.JobTrackerAPI5;

public class JobActivitySeries : JTObject
{
	private enum JobActivitySeriesConditionalFieldUpdateFlags_Enum
	{
		cfufJobActivitySeriesName = 1,
		cfufWorkDays = 2,
		cfufScheduledTime = 4
	}

	public enum WorkDays_Enum
	{
		None = 0,
		Monday = 1,
		Tuesday = 2,
		Wednesday = 4,
		Thursday = 8,
		Friday = 16,
		Saturday = 32,
		Sunday = 64,
		WeekDays = 31,
		All = 79
	}

	private string _jobActivitySeriesName;

	private WorkDays_Enum m_workDays;

	private int m_length;

	private int m_activityTypeId;

	private string m_activityTypeName;

	private DateTime? m_scheduledTime;

	public WorkDays_Enum WorkDays
	{
		get
		{
			return m_workDays;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			m_workDays = value;
		}
	}

	internal bool ModifiedWorkDays => base.UpdateFlags.AreFlagsSet(2);

	public int Length => m_length;

	public int ActivityTypeId => m_activityTypeId;

	public string ActivityTypeName => m_activityTypeName;

	public DateTime? ScheduledTime
	{
		get
		{
			return m_scheduledTime;
		}
		set
		{
			if (value.HasValue)
			{
				string strA = value.Value.ToString("HH:mm");
				if (((value.Value.Minute != 0) & (value.Value.Minute != 30)) || string.CompareOrdinal(strA, "06:00") < 0)
				{
					throw new Exception("Invalid ScheduledTime for JobActivitySeries:  \"" + value.Value.ToString("HH:mm") + "\".");
				}
			}
			base.UpdateFlags.AddUpdateFlag(4);
			m_scheduledTime = value;
		}
	}

	internal bool ModifiedScheduledTime => base.UpdateFlags.AreFlagsSet(4);

	public int JobId { get; }

	public string JobName { get; }

	public int JobActivitySeriesId { get; }

	public string JobActivitySeriesName
	{
		get
		{
			return _jobActivitySeriesName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_jobActivitySeriesName = value;
		}
	}

	internal bool ModifiedJobActivitySeriesName => base.UpdateFlags.AreFlagsSet(1);

	private static void AddStringIfFlagSet(int flagsToTestFor_, int flagsToTest_, StringBuilder stringBuilder_, string string_, string listSeparator_ = ", ")
	{
		if (Connection.AreAllFlagsSet(flagsToTestFor_, flagsToTest_))
		{
			if (stringBuilder_.Length > 0)
			{
				stringBuilder_.Append(listSeparator_);
			}
			stringBuilder_.Append(string_);
		}
	}

	public static string DisplayableWorkDays(WorkDays_Enum workDays_, string listSeparator_ = ", ")
	{
		StringBuilder stringBuilder = new StringBuilder();
		AddStringIfFlagSet(1, (int)workDays_, stringBuilder, "Monday", listSeparator_);
		AddStringIfFlagSet(2, (int)workDays_, stringBuilder, "Tuesday", listSeparator_);
		AddStringIfFlagSet(4, (int)workDays_, stringBuilder, "Wednesday", listSeparator_);
		AddStringIfFlagSet(8, (int)workDays_, stringBuilder, "Thursday", listSeparator_);
		AddStringIfFlagSet(16, (int)workDays_, stringBuilder, "Friday", listSeparator_);
		AddStringIfFlagSet(32, (int)workDays_, stringBuilder, "Saturday", listSeparator_);
		AddStringIfFlagSet(64, (int)workDays_, stringBuilder, "Sunday", listSeparator_);
		return stringBuilder.ToString();
	}

	internal JobActivitySeries(int id_, string name_, int jobId_, string jobName_, int activityTypeId_, string activityTypeName_, int workDays_, int length_, DateTime? scheduledTime_)
	{
		JobActivitySeriesId = id_;
		_jobActivitySeriesName = name_;
		WorkDays = (WorkDays_Enum)(0x4F & workDays_);
		m_length = length_;
		m_activityTypeId = activityTypeId_;
		m_activityTypeName = activityTypeName_;
		ScheduledTime = scheduledTime_;
		JobId = jobId_;
		JobName = jobName_;
		ClearUpdateFlags();
	}

	public JobActivitySeries(int id_)
	{
		JobActivitySeriesId = id_;
		_jobActivitySeriesName = "";
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobActivitySeriesMember
public class JobActivitySeriesMember
{
	public int SeriesId { get; set; }

	public int SeqNum { get; set; }

	public string SeriesName { get; set; }

	public int SeriesLength { get; set; }

	public JobActivitySeriesMember(int seriesId_, int seqNum_, string seriesName_, int seriesLength_)
	{
		SeriesId = seriesId_;
		SeqNum = seqNum_;
		SeriesName = seriesName_;
		SeriesLength = seriesLength_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobActivityStatus
using Moraware.JobTrackerAPI5;

public class JobActivityStatus : JTObject
{
	public enum JobActivityStatusType_Enum
	{
		AutoSchedule,
		Active,
		Complete,
		Canceled
	}

	public string Abbreviation { get; }

	public bool IsInactive { get; }

	public int SeqNum { get; }

	public JobActivityStatusType_Enum JobActivityStatusType { get; }

	public string DisplayColor { get; }

	public bool ConfirmTimeChange { get; }

	public bool ValidForAppointments { get; }

	public int JobActivityStatusId { get; }

	public string JobActivityStatusName { get; }

	internal JobActivityStatus(int id_, string name_, string abbreviation_, bool isInactive_, int seqNum_, JobActivityStatusType_Enum jobActivityStatusType_, string displayColor_, bool confirmTimeChange_, bool validForAppointments_)
	{
		JobActivityStatusId = id_;
		JobActivityStatusName = name_;
		IsInactive = isInactive_;
		SeqNum = seqNum_;
		JobActivityStatusType = jobActivityStatusType_;
		DisplayColor = displayColor_;
		ConfirmTimeChange = confirmTimeChange_;
		ValidForAppointments = validForAppointments_;
		Abbreviation = abbreviation_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobActivityType
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class JobActivityType : JTObject
{
	private List<int> _processes = new List<int>();

	public string Description { get; set; }

	public bool IsInactive { get; set; }

	public int JobActivityTypeId { get; }

	public string JobActivityTypeName { get; }

	public IEnumerable<int> Processes => _processes;

	internal JobActivityType(int id_, string name_, string description_, bool isInactive_, IEnumerable<int> processes_)
	{
		JobActivityTypeId = id_;
		JobActivityTypeName = name_;
		Description = description_;
		IsInactive = isInactive_;
		if (processes_ != null)
		{
			_processes.AddRange(processes_);
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobContact
using Moraware.JobTrackerAPI5;

public class JobContact
{
	public int ContactId { get; set; }

	public Address Address { get; set; }

	internal JobContact(int contactId_, Address address_)
	{
		ContactId = contactId_;
		Address = address_;
	}

	public JobContact(int contactId_)
	{
		ContactId = contactId_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobContactContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class JobContactContainer : IEnumerable<JobContact>, IEnumerable
{
	private List<JobContact> m_contacts = new List<JobContact>();

	private bool m_modified;

	internal bool Modified => m_modified;

	public int Count => m_contacts.Count;

	internal void ClearUpdateFlags()
	{
		m_modified = false;
	}

	public void AddJobContact(JobContact jobContact_)
	{
		m_modified = true;
		m_contacts.Add(jobContact_);
	}

	public void Clear()
	{
		if (Count > 0)
		{
			m_modified = true;
			m_contacts.Clear();
		}
	}

	public IEnumerator<JobContact> GetEnumerator()
	{
		return m_contacts.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator1();
	}

	public IEnumerator GetEnumerator1()
	{
		return m_contacts.GetEnumerator();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobCustomFieldType
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class JobCustomFieldType : CustomFieldType
{
	private List<int> m_processes;

	public IEnumerable<int> Processes => m_processes;

	internal JobCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_, IEnumerable<int> processes_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
		m_processes = new List<int>();
		if (processes_ != null)
		{
			m_processes.AddRange(processes_);
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobFile
using Moraware.JobTrackerAPI5;

public class JobFile : AttachedFile
{
	private enum JobFileConditionalFieldUpdateFlags_Enum
	{
		cfuf_JobPhases = 4
	}

	private JobPhaseContainer m_jobPhases = new JobPhaseContainer();

	public JobPhaseContainer JobPhases
	{
		get
		{
			return m_jobPhases;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			m_jobPhases = value;
		}
	}

	internal bool ModifiedJobPhases
	{
		get
		{
			if (base.UpdateFlags.AreAnyFlagsSet(4))
			{
				return true;
			}
			if (JobPhases == null)
			{
				return false;
			}
			return JobPhases.Modified;
		}
	}

	public int JobId => base.ParentObjectId;

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (JobPhases != null)
		{
			JobPhases.ClearUpdateFlags();
		}
	}

	public JobFile(int id_)
		: base(id_)
	{
	}

	public JobFile(int jobId_, string name_)
		: base(jobId_, name_)
	{
	}

	internal JobFile(int id_, int jobId_, string name_, string description_, int? size_)
		: base(id_, jobId_, name_, description_, size_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobFilter
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class JobFilter
{
	public enum JobListOfValuesFilterFields_Enum
	{
		Salesperson = 1
	}

	public enum JobTextFilterFields_Enum
	{
		Name = 1,
		Notes
	}

	internal CustomFieldFilters ObjCustomFieldFilters { get; } = new CustomFieldFilters();

	internal List<BuiltInTextFilter<JobTextFilterFields_Enum>> TextFilters { get; }

	internal List<BuiltInListOfValuesFilter<JobListOfValuesFilterFields_Enum>> ListOfValuesFilters { get; }

	public int ProcessId { get; set; }

	public int? ViewId { get; set; }

	public Job.JobStatus_Enum? JobStatus { get; set; }

	internal List<CustomFieldFilter> CustomFieldFilters => ObjCustomFieldFilters.CustomFieldFiltersList;

	public void AddListOfValuesFilter(JobListOfValuesFilterFields_Enum field_, ListOfValuesFilter listOfValuesFilter_)
	{
		if (listOfValuesFilter_ != null)
		{
			ListOfValuesFilters.Add(new BuiltInListOfValuesFilter<JobListOfValuesFilterFields_Enum>(field_, listOfValuesFilter_));
		}
	}

	public JobFilter(int processId_ = 1)
	{
		ProcessId = processId_;
		TextFilters = new List<BuiltInTextFilter<JobTextFilterFields_Enum>>();
		ListOfValuesFilters = new List<BuiltInListOfValuesFilter<JobListOfValuesFilterFields_Enum>>();
	}

	public void AddTextFilter(JobTextFilterFields_Enum field_, TextFilter textFilter_)
	{
		if (textFilter_ != null)
		{
			TextFilters.Add(new BuiltInTextFilter<JobTextFilterFields_Enum>(field_, textFilter_));
		}
	}

	public void AddJobCustomFieldFilter(int customFieldId_, ICustomFieldFilter filter_)
	{
		ObjCustomFieldFilters.AddCustomFieldFilter(customFieldId_, filter_, CustomFieldType.CustomFieldType_Enum.Job);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobForm
using Moraware.JobTrackerAPI5;

public class JobForm : JTObject
{
	private enum JobFormConditionalFieldUpdateFlags_Enum
	{
		cfufJobFormName = 1
	}

	private string _jobFormName;

	public JobFormFieldValueContainer FieldValues { get; } = new JobFormFieldValueContainer();

	public int FormTemplateId { get; internal set; }

	public string FormTemplateName { get; internal set; }

	public JobPhaseContainer JobPhases { get; internal set; } = new JobPhaseContainer();

	public int JobId { get; internal set; }

	public int JobFormId { get; internal set; }

	public string JobFormName
	{
		get
		{
			return _jobFormName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_jobFormName = value;
		}
	}

	internal bool ModifiedJobFormName => base.UpdateFlags.AreFlagsSet(1);

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		FieldValues.ClearUpdateFlags();
		if (JobPhases != null)
		{
			JobPhases.ClearUpdateFlags();
		}
	}

	public JobForm(int jobFormId_)
	{
		JobFormId = jobFormId_;
	}

	public JobForm(int jobId_, int formTemplateId_)
	{
		JobId = jobId_;
		FormTemplateId = formTemplateId_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobFormFieldValue
using Moraware.JobTrackerAPI5;

public class JobFormFieldValue : JTObject
{
	internal enum JobFormFieldValueConditionalFieldUpdateFlags_Enum
	{
		cfufValue = 1
	}

	private string _fieldValue;

	private int? _fieldValueId;

	private JobFormFieldValueContainer _jobFormFieldValueContainer;

	internal bool ModifiedValue => base.UpdateFlags.AreFlagsSet(1);

	public string FieldValue
	{
		get
		{
			return _fieldValue;
		}
		set
		{
			SetFieldIdAndValue(null, value);
		}
	}

	public int? FieldValueId
	{
		get
		{
			return _fieldValueId;
		}
		set
		{
			SetFieldIdAndValue(value, null);
		}
	}

	public FormTemplateField.FormFieldDataType_Enum FormFieldDataType { get; }

	public int JobFormFieldId { get; }

	public string JobFormFieldName { get; }

	internal JobFormFieldValue(JobFormFieldValueContainer jobFormFieldValueContainer_, int jobFormFieldId_, string jobFormFieldName_, string formFieldDataTypeName_)
	{
		JobFormFieldId = jobFormFieldId_;
		JobFormFieldName = jobFormFieldName_;
		_jobFormFieldValueContainer = jobFormFieldValueContainer_;
		FormFieldDataType = FormTemplateField.FormFieldDataTypeFromFormFieldDataTypeName(formFieldDataTypeName_);
	}

	public void SetFieldIdAndValue(int? fieldValueId_, string fieldValue_)
	{
		_jobFormFieldValueContainer.Modified = true;
		base.UpdateFlags.AddUpdateFlag(1);
		_fieldValue = fieldValue_;
		_fieldValueId = fieldValueId_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobFormFieldValueContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class JobFormFieldValueContainer : IEnumerable<JobFormFieldValue>, IEnumerable
{
	private Dictionary<int, JobFormFieldValue> _mapById;

	private List<JobFormFieldValue> _list = new List<JobFormFieldValue>();

	internal bool Modified { get; set; }

	internal Dictionary<int, JobFormFieldValue> MapById
	{
		get
		{
			if (_mapById == null)
			{
				_mapById = new Dictionary<int, JobFormFieldValue>();
				foreach (JobFormFieldValue item in _list)
				{
					_mapById.Add(item.JobFormFieldId, item);
				}
			}
			return _mapById;
		}
	}

	internal void Clear()
	{
		_list.Clear();
		if (_mapById != null)
		{
			_mapById = null;
		}
	}

	internal void ClearUpdateFlags()
	{
		Modified = false;
		using IEnumerator<JobFormFieldValue> enumerator = GetEnumerator();
		while (enumerator.MoveNext())
		{
			enumerator.Current.ClearUpdateFlags();
		}
	}

	public JobFormFieldValue ItemAt(int zeroBasedIndex_)
	{
		return _list[zeroBasedIndex_];
	}

	public JobFormFieldValue Item(int id_)
	{
		JobFormFieldValue jobFormFieldValue = null;
		if (MapById.ContainsKey(id_))
		{
			return MapById[id_];
		}
		return null;
	}

	public JobFormFieldValue Item(string name_, bool exceptionIfNotThere_ = false)
	{
		JobFormFieldValue jobFormFieldValue = null;
		using (IEnumerator<JobFormFieldValue> enumerator = GetEnumerator())
		{
			while (enumerator.MoveNext())
			{
				JobFormFieldValue current = enumerator.Current;
				if (name_ == current.JobFormFieldName)
				{
					return current;
				}
			}
		}
		if (exceptionIfNotThere_)
		{
			throw new APIException(null, "No such item (name=\"" + name_ + "\").", APIException.APIErrorCodes_Enum.NonExistentObject);
		}
		return null;
	}

	internal JobFormFieldValue Add(JobFormFieldValue t_)
	{
		if (_mapById != null)
		{
			_mapById.Add(t_.JobFormFieldId, t_);
		}
		_list.Add(t_);
		Modified = true;
		return t_;
	}

	public bool ContainsItemWithId(int id_)
	{
		return MapById.ContainsKey(id_);
	}

	public int Count()
	{
		return _list.Count;
	}

	public IEnumerator<JobFormFieldValue> GetEnumerator()
	{
		return _list.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}

	internal JobFormFieldValue AddJobFormFieldValue(int jobFormFieldId_, string jobFormFieldName_, string formFieldDataTypeName_)
	{
		JobFormFieldValue t_ = new JobFormFieldValue(this, jobFormFieldId_, jobFormFieldName_, formFieldDataTypeName_);
		return Add(t_);
	}

	public void SetFieldValue(int jobFormFieldId_, string fieldValue_)
	{
		JobFormFieldValue jobFormFieldValue = Item(jobFormFieldId_);
		if (jobFormFieldValue == null)
		{
			jobFormFieldValue = Add(new JobFormFieldValue(this, jobFormFieldId_, null, null));
		}
		jobFormFieldValue.FieldValue = fieldValue_;
	}

	public void SetFieldValueId(int jobFormFieldId_, int? fieldValueId_)
	{
		JobFormFieldValue jobFormFieldValue = Item(jobFormFieldId_);
		if (jobFormFieldValue == null)
		{
			jobFormFieldValue = Add(new JobFormFieldValue(this, jobFormFieldId_, null, null));
		}
		jobFormFieldValue.FieldValueId = fieldValueId_;
	}

	public string GetFieldValue(int jobFormFieldId_)
	{
		JobFormFieldValue jobFormFieldValue = Item(jobFormFieldId_);
		if (jobFormFieldValue == null)
		{
			return "";
		}
		return jobFormFieldValue.FieldValue;
	}

	public string GetFieldValue(string jobFormFieldName_)
	{
		JobFormFieldValue jobFormFieldValue = Item(jobFormFieldName_);
		if (jobFormFieldValue == null)
		{
			return "";
		}
		return jobFormFieldValue.FieldValue;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobPhase
using Moraware.JobTrackerAPI5;

public class JobPhase : JTObject
{
	private enum JobPhaseConditionalFieldUpdateFlags_Enum
	{
		cfufJobPhaseName = 1
	}

	private string _jobPhaseName;

	public int SeqNum { get; internal set; }

	public int JobId { get; internal set; }

	public int JobPhaseId { get; internal set; }

	public string JobPhaseName
	{
		get
		{
			return _jobPhaseName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_jobPhaseName = value;
		}
	}

	internal bool ModifiedJobPhaseName => base.UpdateFlags.AreFlagsSet(1);

	public JobPhase(int jobId_, string name_)
	{
		JobId = jobId_;
		JobPhaseName = name_;
	}

	public JobPhase(int jobPhaseId_)
	{
		JobPhaseId = jobPhaseId_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobPhaseContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class JobPhaseContainer : IEnumerable<JobPhase>, IEnumerable
{
	private Dictionary<int, JobPhase> _mapById;

	private List<JobPhase> _list = new List<JobPhase>();

	private bool m_all;

	internal bool Modified { get; set; }

	internal Dictionary<int, JobPhase> MapById
	{
		get
		{
			if (_mapById == null)
			{
				_mapById = new Dictionary<int, JobPhase>();
				foreach (JobPhase item in _list)
				{
					_mapById.Add(item.JobPhaseId, item);
				}
			}
			return _mapById;
		}
	}

	public bool All
	{
		get
		{
			return m_all;
		}
		set
		{
			Modified = true;
			if (value)
			{
				Clear();
			}
			m_all = value;
		}
	}

	public void Clear()
	{
		Modified = true;
		if (All)
		{
			All = false;
		}
		if (_list.Count > 0)
		{
			_list.Clear();
			if (_mapById != null)
			{
				_mapById = null;
			}
		}
	}

	internal void ClearUpdateFlags()
	{
		Modified = false;
		using IEnumerator<JobPhase> enumerator = GetEnumerator();
		while (enumerator.MoveNext())
		{
			enumerator.Current.ClearUpdateFlags();
		}
	}

	public JobPhase ItemAt(int zeroBasedIndex_)
	{
		return _list[zeroBasedIndex_];
	}

	public JobPhase Item(int id_)
	{
		JobPhase jobPhase = null;
		if (MapById.ContainsKey(id_))
		{
			return MapById[id_];
		}
		return null;
	}

	public JobPhase Item(string name_, bool exceptionIfNotThere_ = false)
	{
		JobPhase jobPhase = null;
		using (IEnumerator<JobPhase> enumerator = GetEnumerator())
		{
			while (enumerator.MoveNext())
			{
				JobPhase current = enumerator.Current;
				if (name_ == current.JobPhaseName)
				{
					return current;
				}
			}
		}
		if (exceptionIfNotThere_)
		{
			throw new APIException("No such item (name=\"" + name_ + "\").", APIException.APIErrorCodes_Enum.NonExistentObject);
		}
		return null;
	}

	public bool ContainsItemWithId(int id_)
	{
		return MapById.ContainsKey(id_);
	}

	public int Count()
	{
		return _list.Count;
	}

	public IEnumerator<JobPhase> GetEnumerator()
	{
		return _list.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}

	internal JobPhaseContainer()
	{
	}

	public void Add(JobPhase jobPhase_)
	{
		Modified = true;
		All = false;
		if (_mapById != null)
		{
			_mapById.Add(jobPhase_.JobPhaseId, jobPhase_);
		}
		_list.Add(jobPhase_);
		Modified = true;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JobTemplate
using Moraware.JobTrackerAPI5;

public class JobTemplate : JTObject
{
	private enum JobTemplateConditionalFieldUpdateFlags_Enum
	{
		cfufJobTemplateName = 1
	}

	private string _jobTemplateName;

	public int JobTemplateId { get; }

	public string JobTemplateName
	{
		get
		{
			return _jobTemplateName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_jobTemplateName = value;
		}
	}

	internal bool ModifiedJobTemplateName => base.UpdateFlags.AreFlagsSet(1);

	public JobTemplate(int id_, string name_)
	{
		JobTemplateId = id_;
		_jobTemplateName = name_;
	}

	public override string ToString()
	{
		return JobTemplateName + " (Id=" + JobTemplateId + ")";
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JTObject
using Moraware.JobTrackerAPI5;

public class JTObject
{
	internal UpdateFlags UpdateFlags { get; } = new UpdateFlags();

	internal virtual void ClearUpdateFlags()
	{
		UpdateFlags.ClearUpdateFlags();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.JTProcess
public class JTProcess
{
	public int ProcessId { get; }

	public string ProcessName { get; }

	public string ProcessPluralName { get; }

	public int SeqNum { get; }

	public bool IsInactive { get; }

	internal JTProcess(int processId_, string processName_, string processPluralName_, bool isInactive_, int seqNum_)
	{
		ProcessId = processId_;
		ProcessName = processName_;
		ProcessPluralName = processPluralName_;
		IsInactive = isInactive_;
		SeqNum = seqNum_;
	}

	public override string ToString()
	{
		string text = null;
		text = ((ProcessName != null) ? ProcessName : $"[Process Id={ProcessId}]");
		if (IsInactive)
		{
			text += " [Inactive]";
		}
		return text;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.LabelTemplate
using Moraware.JobTrackerAPI5;

public class LabelTemplate : JTObject
{
	public bool IsInactive { get; set; }

	public int LabelTemplateId { get; }

	public string LabelTemplateName { get; }

	public int SeqNum { get; }

	public decimal PageWidthInches { get; internal set; }

	public decimal PageHeightInches { get; internal set; }

	public decimal MarginTopInches { get; internal set; }

	public decimal MarginBottomInches { get; internal set; }

	public decimal MarginLeftInches { get; internal set; }

	public decimal MarginRightInches { get; internal set; }

	public decimal LabelHeightInches { get; internal set; }

	public decimal LabelWidthInches { get; internal set; }

	public int RowsPerPage { get; internal set; }

	public int ColumnsPerPage { get; internal set; }

	public bool PrintRowsThenColumns { get; internal set; }

	public bool DrawBorder { get; internal set; }

	internal LabelTemplate(int id_, string name_, bool isInactive_, int seqNum_)
	{
		LabelTemplateId = id_;
		LabelTemplateName = name_;
		SeqNum = seqNum_;
		IsInactive = isInactive_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ListOfValuesFilter
using System;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class ListOfValuesFilter : ICustomFieldFilter, IFilter, ICloneable
{
	private GenericListOfValuesFilter<int, ListOfValuesFilterValues> _genericLOVFilter;

	public CustomFieldFilterType_Enum FilterType => CustomFieldFilterType_Enum.ListOfValues;

	public bool Invert
	{
		get
		{
			return _genericLOVFilter.Invert;
		}
		set
		{
			_genericLOVFilter.Invert = value;
		}
	}

	public ListOfValuesFilterValues Values => _genericLOVFilter.Values;

	public ListOfValuesFilter()
		: this(invert_: false, null)
	{
	}

	public ListOfValuesFilter(bool invert_, ListOfValuesFilterValues values_)
	{
		_genericLOVFilter = new GenericListOfValuesFilter<int, ListOfValuesFilterValues>(invert_, values_);
	}

	public ListOfValuesFilter(bool invert_, IEnumerable<int> values_, bool includeNoneInValues_)
		: this(invert_, new ListOfValuesFilterValues(includeNoneInValues_, values_))
	{
	}

	public object Clone()
	{
		return new ListOfValuesFilter(Invert, Values);
	}

	public string BuildDescription(string fieldName_, Dictionary<int, string> lovValues_)
	{
		return _genericLOVFilter.BuildDescription(fieldName_, lovValues_);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ListOfValuesFilterValues
using System;
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class ListOfValuesFilterValues : IGenericListOfValuesFilterValues<int>, IEnumerable<int>, IEnumerable, ICloneable
{
	private GenericNullableListOfValuesFilterValues<int> _genericNullableListOfValuesFilterValues;

	public List<int> Values => _genericNullableListOfValuesFilterValues.Values;

	public bool IncludeNone
	{
		get
		{
			return _genericNullableListOfValuesFilterValues.IncludeNone;
		}
		set
		{
			_genericNullableListOfValuesFilterValues.IncludeNone = value;
		}
	}

	public IEnumerator<int> GetEnumerator()
	{
		return _genericNullableListOfValuesFilterValues.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}

	public IEnumerator GetEnumerator1()
	{
		return _genericNullableListOfValuesFilterValues.GetEnumerator1();
	}

	public ListOfValuesFilterValues()
		: this(includeNone_: false, null)
	{
	}

	public ListOfValuesFilterValues(bool includeNone_)
		: this(includeNone_, null)
	{
	}

	public ListOfValuesFilterValues(bool includeNone_, IEnumerable<int> values_)
	{
		_genericNullableListOfValuesFilterValues = new GenericNullableListOfValuesFilterValues<int>(includeNone_, values_);
	}

	public ListOfValuesFilterValues(IEnumerable<int> values_)
		: this(includeNone_: false, values_)
	{
	}

	bool IGenericListOfValuesFilterValues<int>.DoIncludeNone()
	{
		return DoIncludeNone();
	}

	internal bool DoIncludeNone()
	{
		return _genericNullableListOfValuesFilterValues.DoIncludeNone();
	}

	object ICloneable.Clone()
	{
		return Clone();
	}

	internal virtual object Clone()
	{
		return new ListOfValuesFilterValues(DoIncludeNone(), Values);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Measurement
using Moraware.JobTrackerAPI5;

public class Measurement : JTObject
{
	internal enum MeasureUpdateFlags_Enum
	{
		cfufValue = 1,
		cfufPostUltimate_Measure
	}

	private decimal _value;

	public decimal Value
	{
		get
		{
			return _value;
		}
		set
		{
			_value = value;
			base.UpdateFlags.AddUpdateFlag(1);
		}
	}

	internal bool ModifiedValue => base.UpdateFlags.AreAnyFlagsSet(1);

	public Measurement(decimal value_)
	{
		_value = value_;
	}

	public override string ToString()
	{
		return Value.ToString();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.MeasurementContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class MeasurementContainer : IEnumerable<Measurement>, IEnumerable
{
	private List<Measurement> _measurements = new List<Measurement>();

	private bool _modified;

	internal bool Modified
	{
		get
		{
			bool flag = _modified;
			if (!flag)
			{
				foreach (Measurement measurement in _measurements)
				{
					if (measurement.ModifiedValue)
					{
						flag = true;
						break;
					}
				}
			}
			return flag;
		}
	}

	public int Count => _measurements.Count;

	public Measurement this[int zeroBasedIndex_] => _measurements[zeroBasedIndex_];

	internal void ClearUpdateFlags()
	{
		_modified = false;
	}

	public void AddMeasurement(Measurement measurement_)
	{
		_modified = true;
		_measurements.Add(measurement_);
	}

	public void Clear()
	{
		if (Count > 0)
		{
			_modified = true;
			_measurements.Clear();
		}
	}

	public IEnumerator<Measurement> GetEnumerator()
	{
		return _measurements.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.NumberFilter
using System;
using Moraware.JobTrackerAPI5;

public class NumberFilter : Filter, ICustomFieldFilter, IFilter, ICloneable
{
	private bool _empty;

	private decimal? _minValue;

	private decimal? _maxValue;

	public decimal? MinValue
	{
		get
		{
			return _minValue;
		}
		set
		{
			_minValue = value;
			if (value.HasValue)
			{
				Empty = false;
			}
		}
	}

	public decimal? MaxValue
	{
		get
		{
			return _maxValue;
		}
		set
		{
			_maxValue = value;
			if (value.HasValue)
			{
				Empty = false;
			}
		}
	}

	public bool Empty
	{
		get
		{
			return _empty;
		}
		set
		{
			_empty = value;
			if (value)
			{
				_maxValue = null;
				_minValue = null;
			}
		}
	}

	public CustomFieldFilterType_Enum FilterType => CustomFieldFilterType_Enum.Numbers;

	private NumberFilter(bool empty_, decimal? minValue_, decimal? maxValue_)
	{
		_empty = empty_;
		_minValue = minValue_;
		_maxValue = maxValue_;
	}

	public NumberFilter(bool empty_)
		: this(empty_, null, null)
	{
	}

	public NumberFilter(decimal? minValue_, decimal? maxValue_)
		: this(empty_: false, minValue_, maxValue_)
	{
	}

	public string BuildDescription(string fieldName_)
	{
		string text = null;
		if (Empty)
		{
			return $"{fieldName_} is empty";
		}
		return $"{fieldName_} is between " + (MinValue.HasValue ? MinValue.ToString() : "any number") + " and " + (MaxValue.HasValue ? MaxValue.ToString() : "any number") + ".";
	}

	public override object Clone()
	{
		return new NumberFilter(Empty, MinValue, MaxValue);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PageView
using System;
using Moraware.JobTrackerAPI5;

public class PageView : JTObject
{
	public enum Page_Enum
	{
		PurchaseOrder = 1,
		Jobs,
		Calendar,
		Accounts
	}

	public enum PageViewType_Enum
	{
		MyViews = 1,
		SharedViews,
		ExternalViews
	}

	public int PageViewId { get; }

	public Page_Enum Page { get; }

	public PageViewType_Enum PageViewType { get; }

	public string PageViewName { get; }

	internal static PageViewType_Enum GetViewTypeFromName(string pageViewType_)
	{
		return pageViewType_ switch
		{
			"My Views" => PageViewType_Enum.MyViews, 
			"Shared Views" => PageViewType_Enum.SharedViews, 
			"External Views" => PageViewType_Enum.ExternalViews, 
			_ => throw new Exception($"Unknown page view type:  {pageViewType_}"), 
		};
	}

	internal static string GetViewTypeName(PageViewType_Enum pageViewType_)
	{
		return pageViewType_ switch
		{
			PageViewType_Enum.MyViews => "My Views", 
			PageViewType_Enum.SharedViews => "Shared Views", 
			PageViewType_Enum.ExternalViews => "External Views", 
			_ => throw new Exception($"Unknown page view type:  {pageViewType_} (id={(int)pageViewType_})"), 
		};
	}

	internal static Page_Enum GetPageFromName(string page_)
	{
		return page_ switch
		{
			"Accounts" => Page_Enum.Accounts, 
			"Calendar" => Page_Enum.Calendar, 
			"Jobs" => Page_Enum.Jobs, 
			"Purchase Orders" => Page_Enum.PurchaseOrder, 
			_ => throw new Exception($"Unknown page:  {page_}"), 
		};
	}

	internal static string GetPageName(Page_Enum page_)
	{
		return page_ switch
		{
			Page_Enum.Accounts => "Accounts", 
			Page_Enum.Calendar => "Calendar", 
			Page_Enum.Jobs => "Jobs", 
			Page_Enum.PurchaseOrder => "Purchase Orders", 
			_ => throw new Exception("Unknown page:  " + (int)page_), 
		};
	}

	internal PageView(int pageViewId_, string pageViewName_, Page_Enum page_, PageViewType_Enum pageViewType_)
	{
		Page = page_;
		PageViewId = pageViewId_;
		PageViewName = pageViewName_;
		PageViewType = pageViewType_;
	}

	public override string ToString()
	{
		return PageViewName;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PageViewFilter
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class PageViewFilter
{
	private IEnumerable<PageView.Page_Enum> _pages;

	private IEnumerable<PageView.PageViewType_Enum> _pageViewTypes;

	internal IEnumerable<int> PageViewIds { get; }

	public IEnumerable<PageView.PageViewType_Enum> PageViewTypes
	{
		get
		{
			return _pageViewTypes;
		}
		set
		{
			if (value == null)
			{
				value = new PageView.PageViewType_Enum[0];
			}
			_pageViewTypes = value;
		}
	}

	public IEnumerable<PageView.Page_Enum> Pages
	{
		get
		{
			return _pages;
		}
		set
		{
			if (value == null)
			{
				value = new PageView.Page_Enum[0];
			}
			_pages = value;
		}
	}

	internal PageViewFilter(IEnumerable<int> pageViewIds_, IEnumerable<PageView.Page_Enum> pages_, IEnumerable<PageView.PageViewType_Enum> pageViewTypes_)
	{
		PageViewIds = pageViewIds_;
		_pages = pages_;
		_pageViewTypes = pageViewTypes_;
	}

	public PageViewFilter()
	{
	}

	public PageViewFilter(IEnumerable<PageView.Page_Enum> pages_, IEnumerable<PageView.PageViewType_Enum> pageViewTypes_)
		: this(null, pages_, pageViewTypes_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PagingOptions
public class PagingOptions
{
	public int FirstRecord { get; set; }

	public int PageSize { get; set; }

	public int? TotalRecords { get; internal set; }

	public PagingOptions(int firstRecord_ = 0, int pageSize_ = 30, bool calculateTotalRecords_ = false)
	{
		FirstRecord = firstRecord_;
		PageSize = pageSize_;
		if (calculateTotalRecords_)
		{
			TotalRecords = 0;
		}
		else
		{
			TotalRecords = null;
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PriceList
using Moraware.JobTrackerAPI5;

public class PriceList : JTObject
{
	public bool IsInactive { get; set; }

	public decimal? DefaultTaxPercent { get; set; }

	public int PriceListId { get; }

	public string PriceListName { get; }

	public PriceList(int id_, string name_, decimal? defaultTaxPercent_, bool isInactive_)
	{
		PriceListId = id_;
		PriceListName = name_;
		IsInactive = isInactive_;
		DefaultTaxPercent = defaultTaxPercent_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Product
using Moraware.JobTrackerAPI5;

public class Product : JTObject
{
	internal enum ProductConditionalFieldUpdateFlags_Enum
	{
		cfufName = 1,
		cfufVariantCount = 2,
		cfufPostUltimate_Product = 4
	}

	public int VariantCount { get; }

	public int ProductId { get; }

	public int ProductLineId { get; }

	public string ProductLineName { get; }

	public int ProductFamilyId { get; }

	public string ProductFamilyName { get; }

	public int UnitOfMeasureId { get; }

	public string UnitOfMeasureName { get; }

	public string ProductName { get; }

	public ProductAttributeTypeContainer ProductAttributeTypes { get; } = new ProductAttributeTypeContainer();

	public bool IsInactive { get; }

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (ProductAttributeTypes != null)
		{
			ProductAttributeTypes.ClearUpdateFlags();
		}
	}

	internal Product(int productId_, string productName_, int productLineId_, string productLineName_, int productFamilyId_, string productFamilyName_, int variantCount_, int unitOfMeasureId_, string unitOfMeasureName_, bool isInactive_)
	{
		ProductId = productId_;
		ProductName = productName_;
		ProductFamilyId = productFamilyId_;
		ProductFamilyName = productFamilyName_;
		ProductLineId = productLineId_;
		ProductLineName = productLineName_;
		VariantCount = variantCount_;
		UnitOfMeasureId = unitOfMeasureId_;
		UnitOfMeasureName = unitOfMeasureName_;
		IsInactive = isInactive_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ProductAttributeType
using Moraware.JobTrackerAPI5;

public class ProductAttributeType : JTObject
{
	public bool IsCustomSort { get; }

	public int ProductAttributeTypeId { get; }

	public string ProductAttributeTypeName { get; }

	public string Description { get; }

	internal ProductAttributeType(int productAttributeTypeId_, string productAttributeTypeName_, string description_, bool isCustomSort_)
	{
		ProductAttributeTypeId = productAttributeTypeId_;
		ProductAttributeTypeName = productAttributeTypeName_;
		Description = description_;
		IsCustomSort = isCustomSort_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ProductAttributeTypeContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class ProductAttributeTypeContainer : IEnumerable<ProductAttributeType>, IEnumerable
{
	private List<ProductAttributeType> _productAttributeTypes = new List<ProductAttributeType>();

	private bool _modified;

	internal bool Modified => _modified;

	public int Count => _productAttributeTypes.Count;

	public ProductAttributeType this[int zeroBasedIndex_] => _productAttributeTypes[zeroBasedIndex_];

	internal void ClearUpdateFlags()
	{
		_modified = false;
	}

	internal void AddProductAttributeType(ProductAttributeType ProductAttributeType_)
	{
		_modified = true;
		_productAttributeTypes.Add(ProductAttributeType_);
	}

	internal void Clear()
	{
		if (Count > 0)
		{
			_modified = true;
			_productAttributeTypes.Clear();
		}
	}

	public IEnumerator<ProductAttributeType> GetEnumerator()
	{
		return _productAttributeTypes.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator1();
	}

	public IEnumerator GetEnumerator1()
	{
		return _productAttributeTypes.GetEnumerator();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ProductAttributeValue
public class ProductAttributeValue
{
	public int ProductAttributeValueId { get; }

	public string Value { get; }

	public string Description { get; }

	public int? SeqNum { get; }

	public int ProductAttributeTypeId { get; }

	public string ProductAttributeTypeName { get; }

	public bool IsInactive { get; }

	internal ProductAttributeValue(int productAttributeValueId_, string value_, string description_, int? seqNum_, int productAttributeTypeId_, string productAttributeTypeName_, bool isInactive_)
	{
		ProductAttributeValueId = productAttributeValueId_;
		Value = value_;
		Description = description_;
		SeqNum = seqNum_;
		ProductAttributeTypeId = productAttributeTypeId_;
		ProductAttributeTypeName = productAttributeTypeName_;
		IsInactive = isInactive_;
	}

	public ProductAttributeValue(int productAttributeValueId_)
	{
		ProductAttributeValueId = productAttributeValueId_;
	}

	public ProductAttributeValue(int productAttributeTypeId_, string value_)
	{
		ProductAttributeTypeId = productAttributeTypeId_;
		Value = value_;
	}

	public ProductAttributeValue(string productAttributeTypeName_, string value_)
	{
		ProductAttributeTypeName = productAttributeTypeName_;
		Value = value_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ProductAttributeValueContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class ProductAttributeValueContainer : IEnumerable<ProductAttributeValue>, IEnumerable
{
	private List<ProductAttributeValue> _productAttributeValues = new List<ProductAttributeValue>();

	internal bool Modified { get; private set; }

	public int Count => _productAttributeValues.Count;

	public ProductAttributeValue this[int zeroBasedIndex_] => _productAttributeValues[zeroBasedIndex_];

	internal ProductAttributeValueContainer()
	{
	}

	internal void ClearUpdateFlags()
	{
		Modified = false;
	}

	public void AddProductAttributeValue(ProductAttributeValue productAttributeValue_)
	{
		Modified = true;
		_productAttributeValues.Add(productAttributeValue_);
	}

	internal void Clear()
	{
		if (Count > 0)
		{
			Modified = true;
			_productAttributeValues.Clear();
		}
	}

	public IEnumerator<ProductAttributeValue> GetEnumerator()
	{
		return _productAttributeValues.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator1();
	}

	public IEnumerator GetEnumerator1()
	{
		return _productAttributeValues.GetEnumerator();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ProductFamily
using Moraware.JobTrackerAPI5;

public class ProductFamily : JTObject
{
	internal enum ProductFamilyConditionalFieldUpdateFlags_Enum
	{
		cfufName = 1,
		cfufPostUltimate_ProductFamily
	}

	private int m_productFamilyId;

	private string _productFamilyName;

	public string ProductFamilyName => _productFamilyName;

	public int ProductFamilyId => m_productFamilyId;

	internal bool ModifiedName => base.UpdateFlags.AreFlagsSet(1);

	internal ProductFamily(int productFamilyId_, string productFamilyName_)
	{
		m_productFamilyId = productFamilyId_;
		_productFamilyName = productFamilyName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ProductLine
using Moraware.JobTrackerAPI5;

public class ProductLine : JTObject
{
	internal enum ProductLineConditionalFieldUpdateFlags_Enum
	{
		cfufName = 1,
		cfufPostUltimate_ProductLine
	}

	private string _productLineName;

	public string ProductLineName => _productLineName;

	public int ProductLineId { get; }

	public string ProductFamilyName { get; }

	public int ProductFamilyId { get; }

	internal bool ModifiedName => base.UpdateFlags.AreFlagsSet(1);

	internal ProductLine(int productLineId_, string productLineName_, int productFamilyId_, string productFamilyName_)
	{
		ProductLineId = productLineId_;
		_productLineName = productLineName_;
		ProductFamilyId = productFamilyId_;
		ProductFamilyName = productFamilyName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ProductVariant
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class ProductVariant : JTObject
{
	internal enum ProductVariantConditionalFieldUpdateFlags_Enum
	{
		cfufName = 1,
		cfufPostUltimate_ProductAttributeVariant
	}

	public int ProductVariantId { get; }

	public int ProductId { get; }

	public string ProductName { get; }

	public string ProductVariantName { get; }

	public ProductAttributeValueContainer ProductAttributeValues { get; } = new ProductAttributeValueContainer();

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (ProductAttributeValues != null)
		{
			ProductAttributeValues.ClearUpdateFlags();
		}
	}

	internal ProductVariant(int productId_, IEnumerable<ProductAttributeValue> productAttributeValues_)
	{
		ProductId = productId_;
		if (productAttributeValues_ == null)
		{
			return;
		}
		foreach (ProductAttributeValue item in productAttributeValues_)
		{
			ProductAttributeValues.AddProductAttributeValue(item);
		}
	}

	internal ProductVariant(int productVariantId_, string productVariantName_, int productId_, string productName_)
	{
		ProductVariantId = productVariantId_;
		ProductVariantName = productVariantName_;
		ProductId = productId_;
		ProductName = productName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrder
using System;
using Moraware.JobTrackerAPI5;

public class PurchaseOrder : HasCustomFieldValues
{
	internal enum PurchaseOrderConditionalFieldUpdateFlags_Enum
	{
		cfufPurchaseOrderNumber = 1,
		cfufShipToLocation = 2,
		cfufCostList = 4,
		cfufOrderDate = 8,
		cfufExpectedDeliveryDate = 0x10,
		cfufSupplier = 0x20,
		cfufTaxRate = 0x40,
		cfufStatus = 0x80,
		cfufNotes = 0x100,
		cfufPostUltimate_PurchaseOrder = 0x200
	}

	public enum PurchaseOrderStatusType_Enum
	{
		NotOrdered,
		Ordered,
		PartiallyFilled,
		Received,
		OverFilled
	}

	private string _purchaseOrderNumber;

	private int _shipToLocationId;

	private int _costListId;

	private int _supplierId;

	private DateTime? _orderDate;

	private DateTime? _expectedDeliveryDate;

	private decimal? _taxRate;

	private string _notes;

	internal bool ModifiedNotes => base.UpdateFlags.AreFlagsSet(256);

	public string Notes
	{
		get
		{
			return _notes;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(256);
			_notes = value;
		}
	}

	public int PurchaseOrderId { get; internal set; }

	public string PurchaseOrderNumber
	{
		get
		{
			return _purchaseOrderNumber;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_purchaseOrderNumber = value;
		}
	}

	internal bool ModifiedPurchaseOrderNumber => base.UpdateFlags.AreFlagsSet(1);

	public decimal? TaxRate
	{
		get
		{
			return _taxRate;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(64);
			_taxRate = value;
		}
	}

	internal bool ModifiedTaxRate => base.UpdateFlags.AreFlagsSet(64);

	public PurchaseOrderStatusType_Enum Status { get; private set; }

	public string StatusName { get; private set; }

	public int SupplierId
	{
		get
		{
			return _supplierId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(32);
			_supplierId = value;
			SupplierName = null;
		}
	}

	public string SupplierName { get; private set; }

	internal bool ModifiedSupplier => base.UpdateFlags.AreFlagsSet(32);

	public int ShipToLocationId
	{
		get
		{
			return _shipToLocationId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_shipToLocationId = value;
			ShipToLocationName = null;
		}
	}

	public string ShipToLocationName { get; private set; }

	internal bool ModifiedShipToLocation => base.UpdateFlags.AreFlagsSet(2);

	public int CostListId
	{
		get
		{
			return _costListId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_costListId = value;
			CostListName = null;
		}
	}

	public string CostListName { get; private set; }

	internal bool ModifiedCostList => base.UpdateFlags.AreFlagsSet(4);

	public DateTime? OrderDate
	{
		get
		{
			return _orderDate;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			_orderDate = value;
		}
	}

	internal bool ModifiedOrderDate => base.UpdateFlags.AreFlagsSet(8);

	public DateTime? ExpectedDeliveryDate
	{
		get
		{
			return _expectedDeliveryDate;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(16);
			_expectedDeliveryDate = value;
		}
	}

	internal bool ModifiedExpectedDeliveryDate => base.UpdateFlags.AreFlagsSet(16);

	public PurchaseOrder(int supplierId_, int costListId_)
	{
		SupplierId = supplierId_;
		CostListId = costListId_;
	}

	public PurchaseOrder(int purchaseOrderId_)
	{
		PurchaseOrderId = purchaseOrderId_;
	}

	internal static PurchaseOrderStatusType_Enum POStatusFromString(string poStatus_)
	{
		return poStatus_ switch
		{
			"Not Ordered" => PurchaseOrderStatusType_Enum.NotOrdered, 
			"Ordered" => PurchaseOrderStatusType_Enum.Ordered, 
			"Over-Filled" => PurchaseOrderStatusType_Enum.OverFilled, 
			"Partially Filled" => PurchaseOrderStatusType_Enum.PartiallyFilled, 
			"Received" => PurchaseOrderStatusType_Enum.Received, 
			_ => throw new Exception("Unknown PO Status \"" + poStatus_ + "\"!!!"), 
		};
	}

	internal static string POStatusStringFromId(PurchaseOrderStatusType_Enum poStatus_)
	{
		return poStatus_ switch
		{
			PurchaseOrderStatusType_Enum.NotOrdered => "Not Ordered", 
			PurchaseOrderStatusType_Enum.Ordered => "Ordered", 
			PurchaseOrderStatusType_Enum.OverFilled => "Over-Filled", 
			PurchaseOrderStatusType_Enum.PartiallyFilled => "Partially Filled", 
			PurchaseOrderStatusType_Enum.Received => "Received", 
			_ => throw new Exception("Unknown PO Status, " + (int)poStatus_ + "!!!"), 
		};
	}

	internal void SetStatus(string status_)
	{
		Status = POStatusFromString(status_);
		StatusName = status_;
	}

	internal void SetSupplier(int supplierId_, string supplierName_)
	{
		_supplierId = supplierId_;
		SupplierName = supplierName_;
	}

	internal void SetShipToLocation(int shipToLocationId_, string shipToLocationName_)
	{
		_shipToLocationId = shipToLocationId_;
		ShipToLocationName = shipToLocationName_;
	}

	internal void SetCostList(int costListId_, string costListName_)
	{
		_costListId = costListId_;
		CostListName = costListName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderCustomFieldType
using Moraware.JobTrackerAPI5;

public class PurchaseOrderCustomFieldType : CustomFieldType
{
	internal PurchaseOrderCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderFile
using Moraware.JobTrackerAPI5;

public class PurchaseOrderFile : AttachedFile
{
	public int PurchaseOrderId => base.ParentObjectId;

	public PurchaseOrderFile(int id_)
		: base(id_)
	{
	}

	public PurchaseOrderFile(int purchaseOrderId_, string name_)
		: base(purchaseOrderId_, name_)
	{
	}

	internal PurchaseOrderFile(int id_, int poId_, string name_, string description_, int? size_)
		: base(id_, poId_, name_, description_, size_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderFilter
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class PurchaseOrderFilter
{
	public enum PODateFilterFields_Enum
	{
		OrderDate = 1,
		ExpectedDeliveryDate,
		CompletionDate
	}

	public enum POListOfValuesFilterFields_Enum
	{
		ShipToLocation = 1,
		CostList,
		Supplier
	}

	public enum POTextFilterFields_Enum
	{
		PurchaseOrderNumber = 1
	}

	private CustomFieldFilters _customFieldFilters = new CustomFieldFilters();

	public int? ViewId { get; set; }

	internal List<CustomFieldFilter> CustomFieldFilters => _customFieldFilters.CustomFieldFiltersList;

	internal List<BuiltInDateFilter<PODateFilterFields_Enum>> DateFilters { get; } = new List<BuiltInDateFilter<PODateFilterFields_Enum>>();

	internal List<BuiltInTextFilter<POTextFilterFields_Enum>> TextFilters { get; } = new List<BuiltInTextFilter<POTextFilterFields_Enum>>();

	internal List<BuiltInListOfValuesFilter<POListOfValuesFilterFields_Enum>> ListOfValuesFilters { get; } = new List<BuiltInListOfValuesFilter<POListOfValuesFilterFields_Enum>>();

	internal List<PurchaseOrderStatusFilter> PurchaseOrderStatusFilters { get; } = new List<PurchaseOrderStatusFilter>();

	public void AddPurchaseOrderCustomFieldFilter(int customFieldId_, ICustomFieldFilter filter_)
	{
		_customFieldFilters.AddCustomFieldFilter(customFieldId_, filter_, CustomFieldType.CustomFieldType_Enum.PurchaseOrder);
	}

	public void AddSupplierCustomFieldFilter(int customFieldId_, ICustomFieldFilter filter_)
	{
		_customFieldFilters.AddCustomFieldFilter(customFieldId_, filter_, CustomFieldType.CustomFieldType_Enum.Supplier);
	}

	public void AddPurchaseOrderStatusFilter(PurchaseOrderStatusFilter purchaseOrderStatusFilter_)
	{
		PurchaseOrderStatusFilters.Add(purchaseOrderStatusFilter_);
	}

	public void AddDateFilter(PODateFilterFields_Enum field_, DateFilter dateFilter_)
	{
		if (dateFilter_ != null)
		{
			DateFilters.Add(new BuiltInDateFilter<PODateFilterFields_Enum>(field_, dateFilter_));
		}
	}

	public void AddListOfValuesFilter(POListOfValuesFilterFields_Enum field_, ListOfValuesFilter listOfValuesFilter_)
	{
		if (listOfValuesFilter_ != null)
		{
			ListOfValuesFilters.Add(new BuiltInListOfValuesFilter<POListOfValuesFilterFields_Enum>(field_, listOfValuesFilter_));
		}
	}

	public void AddTextFilter(POTextFilterFields_Enum field_, TextFilter textFilter_)
	{
		if (textFilter_ != null)
		{
			TextFilters.Add(new BuiltInTextFilter<POTextFilterFields_Enum>(field_, textFilter_));
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderLine
using Moraware.JobTrackerAPI5;

public abstract class PurchaseOrderLine : JTObject
{
	public enum PurchaseOrderLineType_Enum
	{
		Miscellaneous = 1,
		Product
	}

	public int PurchaseOrderId { get; }

	public int PurchaseOrderLineId { get; internal set; }

	public PurchaseOrderLineType_Enum PurchaseOrderLineType { get; }

	public string LineDescription { get; internal set; }

	internal PurchaseOrderLine(int purchaseOrderId_, int purchaseOrderLine_, PurchaseOrderLineType_Enum purchaseOrderLineType_)
	{
		PurchaseOrderId = purchaseOrderId_;
		PurchaseOrderLineId = purchaseOrderLine_;
		PurchaseOrderLineType = purchaseOrderLineType_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderMaterialLine
using System;
using Moraware.JobTrackerAPI5;

public abstract class PurchaseOrderMaterialLine : PurchaseOrderLine
{
	internal enum PurchaseOrderMaterialLineConditionalFieldUpdateFlags_Enum
	{
		cfufOrderedQuantity = 1,
		cfufUnitCost = 2,
		cfufIsTaxable = 4,
		cfufPostUltimate_PurchaseOrder = 8
	}

	private decimal _orderedQuantity;

	private decimal _unitCost;

	private string _statusName;

	private bool _isTaxable;

	internal bool ModifiedIsTaxable => base.UpdateFlags.AreFlagsSet(4);

	internal bool ModifiedOrderedQuantity => base.UpdateFlags.AreFlagsSet(1);

	internal bool ModifiedUnitCost => base.UpdateFlags.AreFlagsSet(2);

	public PurchaseOrder.PurchaseOrderStatusType_Enum Status { get; private set; }

	public string StatusName
	{
		get
		{
			return _statusName;
		}
		internal set
		{
			Status = PurchaseOrder.POStatusFromString(value);
			_statusName = value;
		}
	}

	public decimal OrderedQuantity
	{
		get
		{
			return _orderedQuantity;
		}
		set
		{
			_orderedQuantity = value;
			base.UpdateFlags.AddUpdateFlag(1);
		}
	}

	public decimal ReceivedQuantity { get; internal set; }

	public DateTime? DeliveryDate { get; internal set; }

	public decimal TotalUnits { get; internal set; }

	public string UnitName { get; internal set; }

	public decimal UnitCost
	{
		get
		{
			return _unitCost;
		}
		set
		{
			_unitCost = value;
			base.UpdateFlags.AddUpdateFlag(2);
		}
	}

	public string TotalUnitsDescription { get; internal set; }

	public decimal TotalCost { get; internal set; }

	public bool IsTaxable
	{
		get
		{
			return _isTaxable;
		}
		set
		{
			_isTaxable = value;
			base.UpdateFlags.AddUpdateFlag(4);
		}
	}

	internal PurchaseOrderMaterialLine(int poId_, int poLineId_, PurchaseOrderLineType_Enum purchaseOrderLineType_)
		: base(poId_, poLineId_, purchaseOrderLineType_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderMiscellaneousLine
using Moraware.JobTrackerAPI5;

public class PurchaseOrderMiscellaneousLine : PurchaseOrderMaterialLine
{
	internal enum PurchaseOrderMiscellaneousLineUpdateFlags_Enum
	{
		cfufMiscItemDescription = 1,
		cfufPostUltimate_PurchaseOrderMiscellaneousLine
	}

	private string _miscItemDescription;

	public string MiscItemDescription
	{
		get
		{
			return _miscItemDescription;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_miscItemDescription = value;
		}
	}

	internal bool ModifiedMiscItemDescription => base.UpdateFlags.AreAnyFlagsSet(1);

	public PurchaseOrderMiscellaneousLine(int purchaseOrderOrPurchaseOrderLineId_, bool isPOIdForLineCreation_)
		: base(isPOIdForLineCreation_ ? purchaseOrderOrPurchaseOrderLineId_ : 0, (!isPOIdForLineCreation_) ? purchaseOrderOrPurchaseOrderLineId_ : 0, PurchaseOrderLineType_Enum.Miscellaneous)
	{
	}

	internal PurchaseOrderMiscellaneousLine(int poId_, int poLineId_)
		: base(poId_, poLineId_, PurchaseOrderLineType_Enum.Miscellaneous)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderProductLine
using Moraware.JobTrackerAPI5;

public class PurchaseOrderProductLine : PurchaseOrderMaterialLine
{
	public string MeasurementDescription { get; internal set; }

	public MeasurementContainer Measurements { get; } = new MeasurementContainer();

	internal bool ModifiedMeasurements => Measurements.Modified;

	public PurchaseProductVariant PurchaseProductVariant { get; }

	public bool IsSerializable { get; internal set; }

	public bool IsInventoried { get; internal set; }

	public decimal SerializableQuantity { get; internal set; }

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (PurchaseProductVariant != null)
		{
			PurchaseProductVariant.ClearUpdateFlags();
		}
	}

	internal PurchaseOrderProductLine(int poId_, int poLineId_, PurchaseProductVariant purchaseProductVariant_)
		: base(poId_, poLineId_, PurchaseOrderLineType_Enum.Product)
	{
		PurchaseProductVariant = purchaseProductVariant_;
	}

	public PurchaseOrderProductLine(int poId_, PurchaseProductVariant purchaseProductVariant_)
		: base(poId_, 0, PurchaseOrderLineType_Enum.Product)
	{
		PurchaseProductVariant = purchaseProductVariant_;
	}

	public PurchaseOrderProductLine(int purchaseOrderLineId_)
		: base(0, purchaseOrderLineId_, PurchaseOrderLineType_Enum.Product)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderReceipt
using System;
using Moraware.JobTrackerAPI5;

public class PurchaseOrderReceipt : JTObject
{
	internal enum PurchaseOrderReceiptConditionalFieldUpdateFlags_Enum
	{
		cfufQuantity = 1,
		cfufDeliveryDate = 2,
		cfufPostUltimate_PurchaseOrder = 4
	}

	public enum IdType_Enum
	{
		PurchaseOrderReceipt_IdType = 1,
		PurchaseOrder_IdType,
		PurchaseOrderLine_IdType,
		UnreceivedSerialNumber_IdType
	}

	private DateTime _deliveryDate;

	private decimal _quantity;

	public int PurchaseOrderReceiptId { get; internal set; }

	public decimal Quantity
	{
		get
		{
			return _quantity;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_quantity = value;
		}
	}

	internal bool ModifiedQuantity => base.UpdateFlags.AreFlagsSet(1);

	public SerialNumber SerialNumber { get; internal set; }

	internal bool ModifiedSerialNumber
	{
		get
		{
			if (SerialNumber != null)
			{
				if (!SerialNumber.ModifiedBatchNumber && !SerialNumber.ModifiedDescription && !SerialNumber.ModifiedInventoryLocation && !SerialNumber.ModifiedSerialNumberName)
				{
					return SerialNumber.CustomFieldValues.Modified;
				}
				return true;
			}
			return false;
		}
	}

	public DateTime DeliveryDate
	{
		get
		{
			return _deliveryDate;
		}
		set
		{
			_deliveryDate = value;
			base.UpdateFlags.AddUpdateFlag(2);
		}
	}

	internal bool ModifiedDeliveryDate => base.UpdateFlags.AreFlagsSet(2);

	public int PurchaseOrderId { get; }

	public int PurchaseOrderLineId { get; }

	public int? UnreceivedSerialNumberId { get; }

	internal IdType_Enum IdTypeUsedAtCreation { get; }

	public PurchaseOrderReceipt(int id_, IdType_Enum idType_)
		: this(id_, idType_, null)
	{
		if (idType_ == IdType_Enum.PurchaseOrderReceipt_IdType)
		{
			SerialNumber = new SerialNumber();
		}
	}

	public PurchaseOrderReceipt(int unreceivedSerialNumberId_, SerialNumber serialNumber_)
	{
		UnreceivedSerialNumberId = unreceivedSerialNumberId_;
		IdTypeUsedAtCreation = IdType_Enum.UnreceivedSerialNumber_IdType;
		SerialNumber = serialNumber_;
	}

	private PurchaseOrderReceipt(int id_, IdType_Enum idType_, SerialNumber serialNumber_)
	{
		switch (idType_)
		{
		case IdType_Enum.PurchaseOrder_IdType:
			PurchaseOrderId = id_;
			break;
		case IdType_Enum.PurchaseOrderLine_IdType:
			PurchaseOrderLineId = id_;
			break;
		case IdType_Enum.PurchaseOrderReceipt_IdType:
			PurchaseOrderReceiptId = id_;
			break;
		case IdType_Enum.UnreceivedSerialNumber_IdType:
			UnreceivedSerialNumberId = id_;
			break;
		}
		IdTypeUsedAtCreation = idType_;
		SerialNumber = serialNumber_;
	}

	public PurchaseOrderReceipt(int purchaseOrderLineId_, decimal quantity_)
		: this(purchaseOrderLineId_, IdType_Enum.PurchaseOrderLine_IdType)
	{
		Quantity = quantity_;
	}

	public PurchaseOrderReceipt(int purchaseOrderLineOrUnreceivedSerialNumberId_, bool isPurchaseOrderLine_, decimal quantity_, SerialNumber serialNumber_)
		: this(purchaseOrderLineOrUnreceivedSerialNumberId_, isPurchaseOrderLine_ ? IdType_Enum.PurchaseOrderLine_IdType : IdType_Enum.UnreceivedSerialNumber_IdType, serialNumber_)
	{
		Quantity = quantity_;
	}

	internal PurchaseOrderReceipt(int purchaseOrderReceiptId_, int purchaseOrderId_, int purchaseOrderLineId_, decimal quantity_, DateTime deliveryDate_, SerialNumber serialNumber_)
	{
		PurchaseOrderReceiptId = purchaseOrderReceiptId_;
		PurchaseOrderId = purchaseOrderId_;
		PurchaseOrderLineId = purchaseOrderLineId_;
		_quantity = quantity_;
		_deliveryDate = deliveryDate_;
		SerialNumber = serialNumber_;
		IdTypeUsedAtCreation = IdType_Enum.PurchaseOrderReceipt_IdType;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderSplitLine
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class PurchaseOrderSplitLine
{
	public class SplitMeasurement
	{
		public List<int> PurchaseOrderReceiptIds { get; }

		public List<int> UnreceivedSerialNumberIds { get; }

		public decimal? AvailableQuantity { get; }

		public List<Measurement> Measurements { get; }

		public int NewPurchaseOrderLineId { get; internal set; }

		public SplitMeasurement(decimal quantity_, IEnumerable<Measurement> measurements_)
		{
			AvailableQuantity = quantity_;
			Measurements = modGlobals.CreateListFromEnumeration(measurements_);
		}

		public SplitMeasurement(int unreceivedSerialNumberId_, IEnumerable<Measurement> measurements_)
			: this(null, measurements_, new int[1] { unreceivedSerialNumberId_ }, null)
		{
		}

		public SplitMeasurement(IEnumerable<int> unreceivedSerialNumberIds_, IEnumerable<Measurement> measurements_)
			: this(null, measurements_, unreceivedSerialNumberIds_, null)
		{
		}

		public SplitMeasurement(decimal? availableQuantity_, IEnumerable<Measurement> measurements_, IEnumerable<int> unreceivedSerialNumberIds_, IEnumerable<int> purchaseOrderReceiptIds_)
		{
			PurchaseOrderReceiptIds = modGlobals.CreateListFromEnumeration(purchaseOrderReceiptIds_);
			UnreceivedSerialNumberIds = modGlobals.CreateListFromEnumeration(unreceivedSerialNumberIds_);
			AvailableQuantity = availableQuantity_;
			Measurements = modGlobals.CreateListFromEnumeration(measurements_);
		}
	}

	public int PurchaseOrderLineId { get; }

	public List<SplitMeasurement> SplitMeasurements { get; } = new List<SplitMeasurement>();

	public PurchaseOrderSplitLine(int purchaseOrderLineId_, SplitMeasurement splitMeasurements_)
		: this(purchaseOrderLineId_, new SplitMeasurement[1] { splitMeasurements_ })
	{
	}

	public PurchaseOrderSplitLine(int purchaseOrderLineId_, IEnumerable<SplitMeasurement> splitMeasurements_)
	{
		PurchaseOrderLineId = purchaseOrderLineId_;
		if (splitMeasurements_ == null)
		{
			return;
		}
		foreach (SplitMeasurement item in splitMeasurements_)
		{
			SplitMeasurements.Add(item);
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderStatusFilter
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class PurchaseOrderStatusFilter : Filter
{
	private GenericListOfValuesFilter<PurchaseOrder.PurchaseOrderStatusType_Enum, PurchaseOrderStatusFilterValues> _genericLOVFilter;

	public bool Invert
	{
		get
		{
			return _genericLOVFilter.Invert;
		}
		set
		{
			_genericLOVFilter.Invert = value;
		}
	}

	public PurchaseOrderStatusFilterValues Values => _genericLOVFilter.Values;

	public PurchaseOrderStatusFilter()
		: this(invert_: false, null)
	{
	}

	public PurchaseOrderStatusFilter(bool invert_, PurchaseOrderStatusFilterValues values_)
	{
		_genericLOVFilter = new GenericListOfValuesFilter<PurchaseOrder.PurchaseOrderStatusType_Enum, PurchaseOrderStatusFilterValues>(invert_, values_);
	}

	public PurchaseOrderStatusFilter(bool invert_, IEnumerable<PurchaseOrder.PurchaseOrderStatusType_Enum> values_)
		: this(invert_, new PurchaseOrderStatusFilterValues(values_))
	{
	}

	public PurchaseOrderStatusFilter(bool invert_, PurchaseOrder.PurchaseOrderStatusType_Enum value_)
		: this(invert_, new PurchaseOrder.PurchaseOrderStatusType_Enum[1] { value_ })
	{
	}

	public PurchaseOrderStatusFilter(PurchaseOrder.PurchaseOrderStatusType_Enum value_)
		: this(invert_: false, new PurchaseOrder.PurchaseOrderStatusType_Enum[1] { value_ })
	{
	}

	public override object Clone()
	{
		return new PurchaseOrderStatusFilter(Invert, Values);
	}

	public string BuildDescription(string fieldName_)
	{
		return _genericLOVFilter.BuildDescription(fieldName_, modGlobals.BuildDictionaryFromEnumeration(new PurchaseOrder.PurchaseOrderStatusType_Enum[5]
		{
			PurchaseOrder.PurchaseOrderStatusType_Enum.NotOrdered,
			PurchaseOrder.PurchaseOrderStatusType_Enum.Ordered,
			PurchaseOrder.PurchaseOrderStatusType_Enum.OverFilled,
			PurchaseOrder.PurchaseOrderStatusType_Enum.PartiallyFilled,
			PurchaseOrder.PurchaseOrderStatusType_Enum.Received
		}));
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseOrderStatusFilterValues
using System;
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class PurchaseOrderStatusFilterValues : IGenericListOfValuesFilterValues<PurchaseOrder.PurchaseOrderStatusType_Enum>, IEnumerable<PurchaseOrder.PurchaseOrderStatusType_Enum>, IEnumerable, ICloneable
{
	private GenericListOfValuesFilterValues<PurchaseOrder.PurchaseOrderStatusType_Enum> _genericLOVFilterValues;

	public List<PurchaseOrder.PurchaseOrderStatusType_Enum> Values => _genericLOVFilterValues.Values;

	List<PurchaseOrder.PurchaseOrderStatusType_Enum> IGenericListOfValuesFilterValues<PurchaseOrder.PurchaseOrderStatusType_Enum>.Values => Values;

	public IEnumerator<PurchaseOrder.PurchaseOrderStatusType_Enum> GetEnumerator()
	{
		return _genericLOVFilterValues.GetEnumerator();
	}

	IEnumerator<PurchaseOrder.PurchaseOrderStatusType_Enum> IEnumerable<PurchaseOrder.PurchaseOrderStatusType_Enum>.GetEnumerator()
	{
		return GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator();
	}

	public PurchaseOrderStatusFilterValues()
	{
	}

	public PurchaseOrderStatusFilterValues(IEnumerable<PurchaseOrder.PurchaseOrderStatusType_Enum> values_)
	{
		_genericLOVFilterValues = new GenericListOfValuesFilterValues<PurchaseOrder.PurchaseOrderStatusType_Enum>(values_);
	}

	bool IGenericListOfValuesFilterValues<PurchaseOrder.PurchaseOrderStatusType_Enum>.DoIncludeNone()
	{
		return DoIncludeNone();
	}

	internal bool DoIncludeNone()
	{
		return _genericLOVFilterValues.DoIncludeNone();
	}

	public object Clone()
	{
		return new PurchaseOrderStatusFilterValues(Values);
	}

	object ICloneable.Clone()
	{
		return Clone();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseProduct
using Moraware.JobTrackerAPI5;

public class PurchaseProduct : Product
{
	internal enum PurchaseProductConditionalFieldUpdateFlags_Enum
	{
		cfufPrintBarcode = 4,
		cfufIsSerializable = 8,
		cfufIsTaxable = 0x10,
		cfufIsInventoried = 0x20,
		cfufPostUltimate_Product = 0x40
	}

	public bool PrintBarcode { get; }

	public bool IsSerializable { get; }

	public bool IsTaxable { get; }

	public bool IsInventoried { get; }

	internal PurchaseProduct(int productId_, string productName_, int productLineId_, string productLineName_, int productFamilyId_, string productFamilyName_, bool isInventoried_, bool isSerialized_, bool isTaxable_, bool printBarcode_, int variantCount_, int unitOfMeasureId_, string unitOfMeasureName_, bool isInactive_)
		: base(productId_, productName_, productLineId_, productLineName_, productFamilyId_, productFamilyName_, variantCount_, unitOfMeasureId_, unitOfMeasureName_, isInactive_)
	{
		IsInventoried = isInventoried_;
		IsSerializable = isSerialized_;
		IsTaxable = isTaxable_;
		PrintBarcode = printBarcode_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseProductVariant
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class PurchaseProductVariant : ProductVariant
{
	internal PurchaseProductVariant(int productVariantId_, string productVariantName_, int productId_, string productName_)
		: base(productVariantId_, productVariantName_, productId_, productName_)
	{
	}

	public PurchaseProductVariant(int purchaseProductId_, IEnumerable<ProductAttributeValue> productAttributeValues_)
		: base(purchaseProductId_, productAttributeValues_)
	{
	}

	public PurchaseProductVariant(int purchaseProductVariantId_)
		: this(purchaseProductVariantId_, null, 0, null)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseProductVariantAllocation
using Moraware.JobTrackerAPI5;

public class PurchaseProductVariantAllocation : Allocation
{
	internal PurchaseProductVariantAllocation(PurchaseProductVariant ppvForCreate_, int pvId_, string pvName_, int jobId_, string jobName_, int jaId_, int atId_, string atName_, decimal quantity_)
		: base(ppvForCreate_, pvId_, pvName_, jobId_, jobName_, jaId_, atId_, atName_, quantity_)
	{
	}

	public PurchaseProductVariantAllocation(int jobActivityId_, int purchaseProductVariantId_, decimal quantity_)
		: this(null, purchaseProductVariantId_, null, 0, null, jobActivityId_, 0, null, quantity_)
	{
	}

	public PurchaseProductVariantAllocation(int jobActivityId_, PurchaseProductVariant purchaseProductVariant_, decimal quantity_)
		: this(purchaseProductVariant_, 0, null, 0, null, jobActivityId_, 0, null, quantity_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.PurchaseProductVariantInventoryAdjustment
using System;
using Moraware.JobTrackerAPI5;

public class PurchaseProductVariantInventoryAdjustment : JTObject
{
	internal enum RemnantConditionalFieldUpdateFlags_Enum
	{
		cfufDescription = 1,
		cfufAdjustmentDate = 2,
		cfufQuantity = 4,
		cfufPostUltimate_PurchaseOrder = 8
	}

	private decimal _quantity;

	private DateTime _adjustmentDate;

	private string _description;

	public decimal Quantity
	{
		get
		{
			return _quantity;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_quantity = value;
		}
	}

	internal bool ModifiedQuantity => base.UpdateFlags.AreFlagsSet(4);

	public int PurchaseProductVariantInventoryAdjustmentId { get; internal set; }

	public string Description
	{
		get
		{
			return _description;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_description = value;
		}
	}

	internal bool ModifiedDescription => base.UpdateFlags.AreFlagsSet(1);

	public PurchaseProductVariant PurchaseProductVariant { get; }

	public DateTime AdjustmentDate
	{
		get
		{
			return _adjustmentDate;
		}
		set
		{
			_adjustmentDate = value;
			base.UpdateFlags.AddUpdateFlag(2);
		}
	}

	internal bool ModifiedAdjustmentDate => base.UpdateFlags.AreFlagsSet(2);

	internal bool PrepedToCreateByPVId { get; }

	internal int PurchaseProductId { get; }

	internal int PurchaseProductVariantId { get; }

	internal ProductAttributeValueContainer ProductAttributeValues { get; } = new ProductAttributeValueContainer();

	internal PurchaseProductVariantInventoryAdjustment(int purchaseProductVariantInventoryAdjustmentId_, DateTime adjustmentDate_, decimal quantity_, string description_, PurchaseProductVariant purchaseProductVariant_)
	{
		PurchaseProductVariantInventoryAdjustmentId = purchaseProductVariantInventoryAdjustmentId_;
		_description = description_;
		_adjustmentDate = adjustmentDate_;
		PurchaseProductVariant = purchaseProductVariant_;
		_quantity = quantity_;
	}

	public PurchaseProductVariantInventoryAdjustment(int purchaseProductVariantInventoryAdjustmentId_)
		: this(purchaseProductVariantInventoryAdjustmentId_, DateTime.Now, 0m, "", new PurchaseProductVariant(0))
	{
	}

	public PurchaseProductVariantInventoryAdjustment(PurchaseProductVariant purchaseProductVariant_)
		: this(0, DateTime.Now.Date, 0m, "", purchaseProductVariant_)
	{
		if (purchaseProductVariant_.ProductVariantId == 0)
		{
			PurchaseProductId = purchaseProductVariant_.ProductId;
			{
				foreach (ProductAttributeValue productAttributeValue in purchaseProductVariant_.ProductAttributeValues)
				{
					ProductAttributeValues.AddProductAttributeValue(productAttributeValue);
				}
				return;
			}
		}
		PrepedToCreateByPVId = true;
		PurchaseProductVariantId = purchaseProductVariant_.ProductVariantId;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.QuoteCustomFieldType
using Moraware.JobTrackerAPI5;

internal class QuoteCustomFieldType : CustomFieldType
{
	internal QuoteCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.QuoteFile
using Moraware.JobTrackerAPI5;

internal class QuoteFile : AttachedFile
{
	public int QuoteId => base.ParentObjectId;

	public QuoteFile(int id_)
		: base(id_)
	{
	}

	public QuoteFile(int quoteId_, string name_)
		: base(quoteId_, name_)
	{
	}

	internal QuoteFile(int id_, int quoteId_, string name_, string description_, int? size_)
		: base(id_, quoteId_, name_, description_, size_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ReadonlyMeasurementContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class ReadonlyMeasurementContainer : IEnumerable<Measurement>, IEnumerable
{
	private List<Measurement> _measurements = new List<Measurement>();

	public int Count => _measurements.Count;

	public Measurement this[int zeroBasedIndex_] => _measurements[zeroBasedIndex_];

	internal void AddMeasurement(Measurement measurement_)
	{
		_measurements.Add(measurement_);
	}

	internal void Clear()
	{
		if (Count > 0)
		{
			_measurements.Clear();
		}
	}

	public IEnumerator<Measurement> GetEnumerator()
	{
		return _measurements.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator1();
	}

	public IEnumerator GetEnumerator1()
	{
		return _measurements.GetEnumerator();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Resources
using System.CodeDom.Compiler;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.Resources;
using System.Runtime.CompilerServices;
using Moraware.JobTrackerAPI5;

[GeneratedCode("System.Resources.Tools.StronglyTypedResourceBuilder", "15.0.0.0")]
[DebuggerNonUserCode]
[CompilerGenerated]
internal class Resources
{
	private static ResourceManager resourceMan;

	private static CultureInfo resourceCulture;

	[EditorBrowsable(EditorBrowsableState.Advanced)]
	internal static ResourceManager ResourceManager
	{
		get
		{
			if (resourceMan == null)
			{
				resourceMan = new ResourceManager("Moraware.JobTrackerAPI5.Resources", typeof(Resources).Assembly);
			}
			return resourceMan;
		}
	}

	[EditorBrowsable(EditorBrowsableState.Advanced)]
	internal static CultureInfo Culture
	{
		get
		{
			return resourceCulture;
		}
		set
		{
			resourceCulture = value;
		}
	}

	internal Resources()
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Salesperson
using Moraware.JobTrackerAPI5;

public class Salesperson : JTObject
{
	internal enum SalespersonConditionalFieldUpdateFlags_Enum
	{
		cfufSalespersonName = 1,
		cfufAccountingId = 2,
		cfufIsInactive = 4,
		cfufPostUltimate_Salesperson = 8
	}

	private int _salespersonId;

	private string _salespersonName;

	private string _accountingId;

	private bool _isInactive;

	internal bool ModifiedAccountingId => base.UpdateFlags.AreFlagsSet(2);

	internal bool ModifiedIsInactive => base.UpdateFlags.AreFlagsSet(4);

	public bool IsInactive
	{
		get
		{
			return _isInactive;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_isInactive = value;
		}
	}

	public string AccountingId
	{
		get
		{
			return _accountingId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_accountingId = value;
		}
	}

	public int SalespersonId => _salespersonId;

	public string SalespersonName
	{
		get
		{
			return _salespersonName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_salespersonName = value;
		}
	}

	internal bool ModifiedSalespersonName => base.UpdateFlags.AreFlagsSet(1);

	public Salesperson(int salespersonId_)
	{
		SetSalespersonId(salespersonId_);
	}

	public Salesperson(string salespersonName_)
	{
		SalespersonName = salespersonName_;
	}

	internal void SetSalespersonId(int id_)
	{
		_salespersonId = id_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SellProduct
using Moraware.JobTrackerAPI5;

public class SellProduct : Product
{
	internal SellProduct(int productId_, string productName_, int productLineId_, string productLineName_, int productFamilyId_, string productFamilyName_, bool isInventoried_, bool isSerialized_, bool isTaxable_, bool printBarcode_, int variantCount_, int unitOfMeasureId_, string unitOfMeasureName_, bool isInactive_)
		: base(productId_, productName_, productLineId_, productLineName_, productFamilyId_, productFamilyName_, variantCount_, unitOfMeasureId_, unitOfMeasureName_, isInactive_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SellProductVariant
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class SellProductVariant : ProductVariant
{
	internal SellProductVariant(int productVariantId_, string productVariantName_, int productId_, string productName_)
		: base(productVariantId_, productVariantName_, productId_, productName_)
	{
	}

	public SellProductVariant(int sellProductId_, IEnumerable<ProductAttributeValue> productAttributeValues_)
		: base(sellProductId_, productAttributeValues_)
	{
	}

	public SellProductVariant(int sellProductVariantId_)
		: this(sellProductVariantId_, null, 0, null)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumber
using Moraware.JobTrackerAPI5;

public class SerialNumber : HasCustomFieldValues
{
	internal enum SerialNumberConditionalFieldUpdateFlags_Enum
	{
		cfufSerialNumberName = 1,
		cfufInventoryLocation = 2,
		cfufBatchNumber = 4,
		cfufDescription = 8,
		cfufPostUltimate_SerialNumber = 0x10
	}

	public enum SerialNumberSourceType_Enum
	{
		Received = 1,
		Unreceived,
		Remnant,
		Import
	}

	public enum RemnantType_Enum
	{
		NotRemnant = 1,
		Remnant,
		Import
	}

	private string _serialNumberName;

	private int? _inventoryLocationId;

	private string _batchNumber;

	private string _description;

	public string Description
	{
		get
		{
			return _description;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			_description = value;
		}
	}

	internal bool ModifiedDescription => base.UpdateFlags.AreFlagsSet(8);

	public string BatchNumber
	{
		get
		{
			return _batchNumber;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_batchNumber = value;
		}
	}

	internal bool ModifiedBatchNumber => base.UpdateFlags.AreFlagsSet(4);

	public int SerialNumberId { get; internal set; }

	public string SerialNumberName
	{
		get
		{
			return _serialNumberName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_serialNumberName = value;
		}
	}

	internal bool ModifiedSerialNumberName => base.UpdateFlags.AreFlagsSet(1);

	public int PurchaseProductId { get; private set; }

	public string PurchaseProductName { get; private set; }

	public int PurchaseProductVariantId { get; private set; }

	public string PurchaseProductVariantName { get; private set; }

	public decimal Quantity { get; internal set; }

	public string MeasurementDescription { get; internal set; }

	public ReadonlyMeasurementContainer Measurements { get; } = new ReadonlyMeasurementContainer();

	public int UnitOfMeasureId { get; private set; }

	public string UnitOfMeasureName { get; private set; }

	public int? InventoryLocationId
	{
		get
		{
			return _inventoryLocationId;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			_inventoryLocationId = value;
			InventoryLocationName = null;
		}
	}

	public string InventoryLocationName { get; private set; }

	internal bool ModifiedInventoryLocation => base.UpdateFlags.AreFlagsSet(2);

	public SerialNumberSourceType_Enum SerialNumberSourceType { get; internal set; }

	public int SerialNumberSourceId { get; internal set; }

	public RemnantType_Enum RemnantType { get; internal set; }

	public decimal Balance { get; internal set; }

	public decimal UnitCost { get; internal set; }

	public SerialNumber(int serialNumberId_)
	{
		SerialNumberId = serialNumberId_;
	}

	public SerialNumber()
	{
	}

	internal void SetPurchaseProduct(int purchaseproductId_, string purchaseProductName_)
	{
		PurchaseProductId = purchaseproductId_;
		PurchaseProductName = purchaseProductName_;
	}

	internal void SetProductVariant(int purchaseProductVariantId_, string purchaseProductVariantName_)
	{
		PurchaseProductVariantId = purchaseProductVariantId_;
		PurchaseProductVariantName = purchaseProductVariantName_;
	}

	internal void SetUnitOfMeasure(int unitOfMeasureId_, string unitOfMeasureName_)
	{
		UnitOfMeasureId = unitOfMeasureId_;
		UnitOfMeasureName = unitOfMeasureName_;
	}

	internal void SetInventoryLocation(int? inventoryLocationId_, string inventoryLocationName_)
	{
		_inventoryLocationId = inventoryLocationId_;
		InventoryLocationName = inventoryLocationName_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberAllocation
using Moraware.JobTrackerAPI5;

public class SerialNumberAllocation : Allocation
{
	internal int? NullableSerialNumberId { get; }

	public int SerialNumberId => NullableSerialNumberId ?? 0;

	public string SerialNumberName { get; }

	internal SerialNumberAllocation(int? snId_, string snName_, int pvId_, string pvName_, int jobId_, string jobName_, int jaId_, int atId_, string atName_, decimal quantity_)
		: base(null, pvId_, pvName_, jobId_, jobName_, jaId_, atId_, atName_, quantity_)
	{
		NullableSerialNumberId = snId_;
		SerialNumberName = snName_;
	}

	public SerialNumberAllocation(int jobActivityId_, string serialNumberName_, decimal quantity_)
		: this(null, serialNumberName_, 0, null, 0, null, jobActivityId_, 0, null, quantity_)
	{
	}

	public SerialNumberAllocation(int jobActivityId_, int serialNumberId_, decimal quantity_)
		: this(serialNumberId_, null, 0, null, 0, null, jobActivityId_, 0, null, quantity_)
	{
	}

	public SerialNumberAllocation(int jobActivityId_, string serialNumberName_)
		: this(null, serialNumberName_, 0, null, 0, null, jobActivityId_, 0, null, 0m)
	{
	}

	public SerialNumberAllocation(int jobActivityId_, int serialNumberId_)
		: this(serialNumberId_, null, 0, null, 0, null, jobActivityId_, 0, null, 0m)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberAllocationContainer
using System.Collections;
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class SerialNumberAllocationContainer : IEnumerable<SerialNumberAllocation>, IEnumerable
{
	private List<SerialNumberAllocation> _serialNumberAllocations = new List<SerialNumberAllocation>();

	internal bool Modified { get; set; }

	public int Count => _serialNumberAllocations.Count;

	public SerialNumberAllocation this[int zeroBasedIndex_] => _serialNumberAllocations[zeroBasedIndex_];

	internal void ClearUpdateFlags()
	{
		Modified = false;
	}

	public void AddAllocation(SerialNumberAllocation serialNumberAllocation_)
	{
		if (serialNumberAllocation_ != null)
		{
			Modified = true;
			_serialNumberAllocations.Add(serialNumberAllocation_);
		}
	}

	public void Clear()
	{
		if (Count > 0)
		{
			Modified = true;
			_serialNumberAllocations.Clear();
		}
	}

	public IEnumerator<SerialNumberAllocation> GetEnumerator()
	{
		return _serialNumberAllocations.GetEnumerator();
	}

	IEnumerator IEnumerable.GetEnumerator()
	{
		return GetEnumerator1();
	}

	public IEnumerator GetEnumerator1()
	{
		return _serialNumberAllocations.GetEnumerator();
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberCustomFieldType
using Moraware.JobTrackerAPI5;

public class SerialNumberCustomFieldType : CustomFieldType
{
	internal SerialNumberCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberFile
using Moraware.JobTrackerAPI5;

public class SerialNumberFile : AttachedFile
{
	public int SerialNumberId => base.ParentObjectId;

	public SerialNumberFile(int id_)
		: base(id_)
	{
	}

	public SerialNumberFile(int serialNumberId_, string name_)
		: base(serialNumberId_, name_)
	{
	}

	internal SerialNumberFile(int id_, int serialNumberId_, string name_, string description_, int? size_)
		: base(id_, serialNumberId_, name_, description_, size_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberFilter
using System.Collections.Generic;
using Moraware.JobTrackerAPI5;

public class SerialNumberFilter
{
	public enum SerialNumberListOfValuesFilterFields_Enum
	{
		InventoryLocation = 1
	}

	public enum SerialNumberTextFilterFields_Enum
	{
		Name = 1,
		Description,
		BatchNumber
	}

	private CustomFieldFilters _customFieldFilters = new CustomFieldFilters();

	internal List<BuiltInTextFilter<SerialNumberTextFilterFields_Enum>> TextFilters { get; } = new List<BuiltInTextFilter<SerialNumberTextFilterFields_Enum>>();

	internal List<BuiltInListOfValuesFilter<SerialNumberListOfValuesFilterFields_Enum>> ListOfValuesFilters { get; } = new List<BuiltInListOfValuesFilter<SerialNumberListOfValuesFilterFields_Enum>>();

	internal List<CustomFieldFilter> CustomFieldFilters => _customFieldFilters.CustomFieldFiltersList;

	public void AddTextFilter(SerialNumberTextFilterFields_Enum field_, TextFilter textFilter_)
	{
		if (textFilter_ != null)
		{
			TextFilters.Add(new BuiltInTextFilter<SerialNumberTextFilterFields_Enum>(field_, textFilter_));
		}
	}

	public void AddListOfValuesFilter(SerialNumberListOfValuesFilterFields_Enum field_, ListOfValuesFilter listOfValuesFilter_)
	{
		if (listOfValuesFilter_ != null)
		{
			ListOfValuesFilters.Add(new BuiltInListOfValuesFilter<SerialNumberListOfValuesFilterFields_Enum>(field_, listOfValuesFilter_));
		}
	}

	public void AddSerialNumberCustomFieldFilter(int customFieldId_, ICustomFieldFilter filter_)
	{
		_customFieldFilters.AddCustomFieldFilter(customFieldId_, filter_, CustomFieldType.CustomFieldType_Enum.SerialNumber);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberImport
using System;
using Moraware.JobTrackerAPI5;

public class SerialNumberImport : JTObject
{
	internal enum ImportConditionalFieldUpdateFlags_Enum
	{
		cfufUnitCost = 1,
		cfufCreationDate = 2,
		cfufQuantity = 4,
		cfufIsRemnant = 8,
		cfufPostUltimate_PurchaseOrder = 0x10
	}

	private decimal _quantity;

	private DateTime _creationDate;

	private bool _isRemnant;

	private decimal _unitCost;

	public decimal Quantity
	{
		get
		{
			return _quantity;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_quantity = value;
		}
	}

	internal bool ModifiedQuantity => base.UpdateFlags.AreFlagsSet(4);

	public int SerialNumberImportId { get; internal set; }

	public decimal UnitCost
	{
		get
		{
			return _unitCost;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_unitCost = value;
		}
	}

	internal bool ModifiedUnitCost => base.UpdateFlags.AreFlagsSet(1);

	public SerialNumber SerialNumber { get; internal set; }

	internal bool ModifiedSerialNumber
	{
		get
		{
			if (SerialNumber != null)
			{
				if (!SerialNumber.ModifiedBatchNumber && !SerialNumber.ModifiedDescription && !SerialNumber.ModifiedInventoryLocation && !SerialNumber.ModifiedSerialNumberName)
				{
					return SerialNumber.CustomFieldValues.Modified;
				}
				return true;
			}
			return false;
		}
	}

	public DateTime CreationDate
	{
		get
		{
			return _creationDate;
		}
		set
		{
			_creationDate = value;
			base.UpdateFlags.AddUpdateFlag(2);
		}
	}

	internal bool ModifiedCreationDate => base.UpdateFlags.AreFlagsSet(2);

	public bool IsRemnant
	{
		get
		{
			return _isRemnant;
		}
		set
		{
			_isRemnant = value;
			base.UpdateFlags.AddUpdateFlag(8);
		}
	}

	internal bool ModifiedIsRemnant => base.UpdateFlags.AreFlagsSet(8);

	public MeasurementContainer Measurements { get; } = new MeasurementContainer();

	internal bool ModifiedMeasurements => Measurements.Modified;

	internal bool PrepedToCreateByPVId { get; }

	internal int PurchaseProductId { get; }

	internal int PurchaseProductVariantId { get; private set; }

	internal ProductAttributeValueContainer ProductAttributeValues { get; } = new ProductAttributeValueContainer();

	internal SerialNumberImport(int serialNumberImportId_, int purchaseProductVariantId_, decimal unitCost_, DateTime creationDate_, SerialNumber serialNumber_, decimal quantity_, bool isRemnant_)
	{
		SerialNumberImportId = serialNumberImportId_;
		PurchaseProductVariantId = purchaseProductVariantId_;
		_unitCost = unitCost_;
		_creationDate = creationDate_;
		SerialNumber = serialNumber_;
		_quantity = quantity_;
		_isRemnant = isRemnant_;
	}

	public SerialNumberImport(int serialNumberImportId_)
		: this(serialNumberImportId_, 0, 0m, DateTime.Now.Date, new SerialNumber(), 0m, isRemnant_: false)
	{
	}

	public SerialNumberImport(PurchaseProductVariant purchaseProductVariant_)
		: this(0, purchaseProductVariant_.ProductVariantId, 0m, DateTime.Now.Date, new SerialNumber(), 0m, isRemnant_: false)
	{
		if (purchaseProductVariant_.ProductVariantId == 0)
		{
			PurchaseProductId = purchaseProductVariant_.ProductId;
			{
				foreach (ProductAttributeValue productAttributeValue in purchaseProductVariant_.ProductAttributeValues)
				{
					ProductAttributeValues.AddProductAttributeValue(productAttributeValue);
				}
				return;
			}
		}
		PrepedToCreateByPVId = true;
		PurchaseProductVariantId = purchaseProductVariant_.ProductVariantId;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberInventoryAdjustment
using System;
using Moraware.JobTrackerAPI5;

public class SerialNumberInventoryAdjustment : JTObject
{
	internal enum RemnantConditionalFieldUpdateFlags_Enum
	{
		cfufDescription = 1,
		cfufAdjustmentDate = 2,
		cfufQuantity = 4,
		cfufPostUltimate_PurchaseOrder = 8
	}

	private int m_serialNumberInventoryAdjustmentId;

	private decimal m_quantity;

	private DateTime m_adjustmentDate;

	private string m_description;

	private SerialNumber m_serialNumber;

	public decimal Quantity
	{
		get
		{
			return m_quantity;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			m_quantity = value;
		}
	}

	internal bool ModifiedQuantity => base.UpdateFlags.AreFlagsSet(4);

	public int SerialNumberInventoryAdjustmentId => m_serialNumberInventoryAdjustmentId;

	public string Description
	{
		get
		{
			return m_description;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			m_description = value;
		}
	}

	internal bool ModifiedDescription => base.UpdateFlags.AreFlagsSet(1);

	public SerialNumber SerialNumber => m_serialNumber;

	internal bool ModifiedSerialNumber
	{
		get
		{
			if (SerialNumber != null)
			{
				if (!SerialNumber.ModifiedBatchNumber && !SerialNumber.ModifiedDescription && !SerialNumber.ModifiedInventoryLocation && !SerialNumber.ModifiedSerialNumberName)
				{
					return SerialNumber.CustomFieldValues.Modified;
				}
				return true;
			}
			return false;
		}
	}

	public DateTime AdjustmentDate
	{
		get
		{
			return m_adjustmentDate;
		}
		set
		{
			m_adjustmentDate = value;
			base.UpdateFlags.AddUpdateFlag(2);
		}
	}

	internal bool ModifiedAdjustmentDate => base.UpdateFlags.AreFlagsSet(2);

	internal SerialNumberInventoryAdjustment(int serialNumberInventoryAdjustmentId_, DateTime adjustmentDate_, decimal quantity_, string description_, SerialNumber serialNumber_)
	{
		m_serialNumberInventoryAdjustmentId = serialNumberInventoryAdjustmentId_;
		m_description = description_;
		m_adjustmentDate = adjustmentDate_;
		m_serialNumber = serialNumber_;
		m_quantity = quantity_;
	}

	public SerialNumberInventoryAdjustment(int serialNumberInventoryAdjustmentOrSerialNumberId_, bool isNewSerialNumberInventoryAdjustment_)
		: this((!isNewSerialNumberInventoryAdjustment_) ? serialNumberInventoryAdjustmentOrSerialNumberId_ : 0, DateTime.Now, 0m, "", new SerialNumber(isNewSerialNumberInventoryAdjustment_ ? serialNumberInventoryAdjustmentOrSerialNumberId_ : 0))
	{
	}

	internal void SetSerialNumberInventoryAdjustmentId(int serialNumberInventoryAdjustmentId_)
	{
		m_serialNumberInventoryAdjustmentId = serialNumberInventoryAdjustmentId_;
	}

	internal void SetSerialNumber(SerialNumber serialNumber_)
	{
		m_serialNumber = serialNumber_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SerialNumberRemnant
using System;
using Moraware.JobTrackerAPI5;

public class SerialNumberRemnant : JTObject
{
	internal enum RemnantConditionalFieldUpdateFlags_Enum
	{
		cfufUnitCost = 1,
		cfufCreationDate = 2,
		cfufQuantity = 4,
		cfufPostUltimate_PurchaseOrder = 8
	}

	private decimal _quantity;

	private DateTime _creationDate;

	private decimal _unitCost;

	public decimal Quantity
	{
		get
		{
			return _quantity;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			_quantity = value;
		}
	}

	internal bool ModifiedQuantity => base.UpdateFlags.AreFlagsSet(4);

	public int SerialNumberRemnantId { get; internal set; }

	public decimal UnitCost
	{
		get
		{
			return _unitCost;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			_unitCost = value;
		}
	}

	internal bool ModifiedUnitCost => base.UpdateFlags.AreFlagsSet(1);

	public SerialNumber SerialNumber { get; internal set; }

	internal bool ModifiedSerialNumber
	{
		get
		{
			if (SerialNumber != null)
			{
				if (!SerialNumber.ModifiedBatchNumber && !SerialNumber.ModifiedDescription && !SerialNumber.ModifiedInventoryLocation && !SerialNumber.ModifiedSerialNumberName)
				{
					return SerialNumber.CustomFieldValues.Modified;
				}
				return true;
			}
			return false;
		}
	}

	public DateTime CreationDate
	{
		get
		{
			return _creationDate;
		}
		set
		{
			_creationDate = value;
			base.UpdateFlags.AddUpdateFlag(2);
		}
	}

	internal bool ModifiedCreationDate => base.UpdateFlags.AreFlagsSet(2);

	public MeasurementContainer Measurements { get; } = new MeasurementContainer();

	internal bool ModifiedMeasurements => Measurements.Modified;

	public int ParentSerialNumberId { get; private set; }

	internal SerialNumberRemnant(int serialNumberRemnantId_, int parentSerialNumberId_, decimal unitCost_, DateTime creationDate_, SerialNumber serialNumber_, decimal quantity_)
	{
		SerialNumberRemnantId = serialNumberRemnantId_;
		ParentSerialNumberId = parentSerialNumberId_;
		_unitCost = unitCost_;
		_creationDate = creationDate_;
		SerialNumber = serialNumber_;
		_quantity = quantity_;
	}

	public SerialNumberRemnant(int parentOrSerialNumberRemnantId_, bool isParentSerialNumberId_)
		: this((!isParentSerialNumberId_) ? parentOrSerialNumberRemnantId_ : 0, isParentSerialNumberId_ ? parentOrSerialNumberRemnantId_ : 0, 0m, DateTime.Now.Date, new SerialNumber(), 0m)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ServerAPIVersion
public class ServerAPIVersion
{
	private int m_minSupportedVersion;

	private int m_currentVersion;

	private int? m_prereleaseVersion;

	public int MinSupportedVersion => m_minSupportedVersion;

	public int CurrentVersion => m_currentVersion;

	public int? PrereleaseVersion => m_prereleaseVersion;

	internal ServerAPIVersion(int minSupportedVersion_, int currentVersion_, int? prereleaseVersion_)
	{
		m_minSupportedVersion = minSupportedVersion_;
		m_currentVersion = currentVersion_;
		m_prereleaseVersion = prereleaseVersion_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Settings
using System.CodeDom.Compiler;
using System.Configuration;
using System.Diagnostics;
using System.Drawing;
using System.Runtime.CompilerServices;
using Moraware.JobTrackerAPI5;

[CompilerGenerated]
[GeneratedCode("Microsoft.VisualStudio.Editors.SettingsDesigner.SettingsSingleFileGenerator", "15.5.0.0")]
internal sealed class Settings : ApplicationSettingsBase
{
	private static Settings defaultInstance = (Settings)SettingsBase.Synchronized(new Settings());

	public static Settings Default => defaultInstance;

	[UserScopedSetting]
	[DebuggerNonUserCode]
	public Point defaultProgress_windowPos
	{
		get
		{
			return (Point)this["defaultProgress_windowPos"];
		}
		set
		{
			this["defaultProgress_windowPos"] = value;
		}
	}

	[UserScopedSetting]
	[DebuggerNonUserCode]
	public Size defaultProgress_windowSize
	{
		get
		{
			return (Size)this["defaultProgress_windowSize"];
		}
		set
		{
			this["defaultProgress_windowSize"] = value;
		}
	}

	[UserScopedSetting]
	[DebuggerNonUserCode]
	public Point login_windowPos
	{
		get
		{
			return (Point)this["login_windowPos"];
		}
		set
		{
			this["login_windowPos"] = value;
		}
	}

	[UserScopedSetting]
	[DebuggerNonUserCode]
	public Size login_windowSize
	{
		get
		{
			return (Size)this["login_windowSize"];
		}
		set
		{
			this["login_windowSize"] = value;
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.ShipToLocation
using Moraware.JobTrackerAPI5;

public class ShipToLocation : JTObject
{
	internal enum ShipToLocationConditionalFieldUpdateFlags_Enum
	{
		cfufShipToLocationName = 1,
		cfufAddress = 2,
		cfufSeqNum = 4,
		cfufIsInactive = 8,
		cfufPostUltimate_ShipToLocation = 0x10
	}

	private Address m_address;

	private int m_shipToLocationId;

	private string m_shipToLocationName;

	private int m_seqNum;

	private bool m_isInactive;

	internal bool ModifiedIsInactive => base.UpdateFlags.AreFlagsSet(8);

	internal bool ModifiedAddress
	{
		get
		{
			if (base.UpdateFlags.AreFlagsSet(2))
			{
				return true;
			}
			if (Address == null)
			{
				return false;
			}
			return Address.Modified;
		}
	}

	public bool IsInactive
	{
		get
		{
			return m_isInactive;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			m_isInactive = value;
		}
	}

	public Address Address
	{
		get
		{
			return m_address;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			m_address = value;
		}
	}

	public int ShipToLocationId => m_shipToLocationId;

	public string ShipToLocationName
	{
		get
		{
			return m_shipToLocationName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			m_shipToLocationName = value;
		}
	}

	internal bool ModifiedShipToLocationName => base.UpdateFlags.AreFlagsSet(1);

	public int SeqNum => m_seqNum;

	internal override void ClearUpdateFlags()
	{
		base.ClearUpdateFlags();
		if (Address != null)
		{
			Address.ClearUpdateFlags();
		}
	}

	public ShipToLocation(string shipToLocationName_)
	{
		ShipToLocationName = shipToLocationName_;
	}

	public ShipToLocation(int shipToLocationId_)
	{
		SetShipToLocationId(shipToLocationId_);
	}

	internal void SetShipToLocationId(int id_)
	{
		m_shipToLocationId = id_;
	}

	internal void SetSeqNum(int seqNum_)
	{
		m_seqNum = seqNum_;
	}

	public override string ToString()
	{
		return ShipToLocationName;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.Supplier
using Moraware.JobTrackerAPI5;

public class Supplier : HasCustomFieldValues
{
	internal enum SupplierConditionalFieldUpdateFlags_Enum
	{
		cfufSupplierName = 1,
		cfufAddress = 2,
		cfufTaxRate = 4,
		cfufNotes = 8,
		cfufIsInactive = 0x10
	}

	private Address m_address;

	private int m_supplierId;

	private string m_supplierName;

	private decimal? m_taxRate;

	private string m_notes;

	private bool m_isInactive;

	internal bool ModifiedAddress
	{
		get
		{
			if (base.UpdateFlags.AreFlagsSet(2))
			{
				return true;
			}
			if (Address == null)
			{
				return false;
			}
			return Address.Modified;
		}
	}

	internal bool ModifiedNotes => base.UpdateFlags.AreFlagsSet(8);

	public Address Address
	{
		get
		{
			return m_address;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(2);
			m_address = value;
		}
	}

	public string Notes
	{
		get
		{
			return m_notes;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(8);
			m_notes = value;
		}
	}

	public int SupplierId => m_supplierId;

	public string SupplierName
	{
		get
		{
			return m_supplierName;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			m_supplierName = value;
		}
	}

	internal bool ModifiedSupplierName => base.UpdateFlags.AreFlagsSet(1);

	public decimal? TaxRate
	{
		get
		{
			return m_taxRate;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(4);
			m_taxRate = value;
		}
	}

	internal bool ModifiedTaxRate => base.UpdateFlags.AreFlagsSet(4);

	public bool IsInactive
	{
		get
		{
			return m_isInactive;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(16);
			m_isInactive = value;
		}
	}

	internal bool ModifiedIsInactive => base.UpdateFlags.AreFlagsSet(16);

	public Supplier(string supplierName_)
	{
		SupplierName = supplierName_;
	}

	public Supplier(int supplierId_)
	{
		SetSupplierId(supplierId_);
	}

	internal void SetSupplierId(int id_)
	{
		m_supplierId = id_;
	}

	public override string ToString()
	{
		return SupplierName;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SupplierCustomFieldType
using Moraware.JobTrackerAPI5;

public class SupplierCustomFieldType : CustomFieldType
{
	internal SupplierCustomFieldType(int id_, string name_, bool isInactive_, bool isCustomSort_, string customFieldDataTypeName_)
		: base(id_, name_, isInactive_, isCustomSort_, customFieldDataTypeName_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.SupplierFile
using Moraware.JobTrackerAPI5;

public class SupplierFile : AttachedFile
{
	public int SupplierId => base.ParentObjectId;

	public SupplierFile(int id_)
		: base(id_)
	{
	}

	public SupplierFile(int supplierId_, string name_)
		: base(supplierId_, name_)
	{
	}

	internal SupplierFile(int id_, int supplierId_, string name_, string description_, int? size_)
		: base(id_, supplierId_, name_, description_, size_)
	{
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.TextFilter
using System;
using Moraware.JobTrackerAPI5;

public class TextFilter : Filter, ICustomFieldFilter, IFilter, ICloneable
{
	private bool m_exactMatch;

	private bool m_empty;

	private string m_searchText;

	public string SearchText
	{
		get
		{
			return m_searchText;
		}
		set
		{
			m_searchText = value;
		}
	}

	public bool ExactMatch
	{
		get
		{
			return m_exactMatch;
		}
		set
		{
			m_exactMatch = value;
		}
	}

	public bool Empty
	{
		get
		{
			return m_empty;
		}
		set
		{
			m_empty = value;
		}
	}

	public CustomFieldFilterType_Enum FilterType => CustomFieldFilterType_Enum.Text;

	private TextFilter(bool empty_, string searchText_, bool exactMatch_)
	{
		m_empty = empty_;
		m_searchText = searchText_;
		m_exactMatch = exactMatch_;
	}

	public TextFilter(bool empty_)
		: this(empty_, null, exactMatch_: false)
	{
	}

	public TextFilter(string searchText_, bool exactMatch_)
		: this(empty_: false, searchText_, exactMatch_)
	{
	}

	public string BuildDescription(string fieldName_)
	{
		string text = null;
		if (Empty)
		{
			return fieldName_ + " is empty";
		}
		return fieldName_ + (ExactMatch ? " exactly matches " : " is like ") + "\"" + SearchText + "\"";
	}

	public override object Clone()
	{
		return new TextFilter(Empty, SearchText, ExactMatch);
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.UnitOfMeasure
using Moraware.JobTrackerAPI5;

public class UnitOfMeasure : JTObject
{
	internal enum UnitOfMeasureConditionalFieldUpdateFlags_Enum
	{
		cfufName = 1,
		cfufMeasurementLabel = 2,
		cfufMeasurementQuantity = 4,
		cfufDivisor = 8,
		cfufMultiplier = 0x10,
		cfufSeqNum = 0x20,
		cfufPostUltimate_UnitOfMeasure = 0x40
	}

	private int m_unitOfMeasureId;

	private string m_unitOfMeasureName;

	private string m_measurementLabel;

	private int m_measurementQuantity;

	private int m_seqNum;

	private decimal m_divisor;

	private decimal m_multiplier;

	public string MeasurementLabel => m_measurementLabel;

	public int MeasurementQuantity => m_measurementQuantity;

	public decimal Divisor => m_divisor;

	public decimal Multiplier => m_multiplier;

	public int SeqNum => m_seqNum;

	public int UnitOfMeasureId => m_unitOfMeasureId;

	public string UnitOfMeasureName => m_unitOfMeasureName;

	public UnitOfMeasure(int unitOfMeasureId_)
	{
		m_unitOfMeasureId = unitOfMeasureId_;
	}

	internal void SetMeasurementLabel(string value)
	{
		base.UpdateFlags.AddUpdateFlag(2);
		m_measurementLabel = value;
	}

	internal void SetMeasurementQuantity(int value_)
	{
		m_measurementQuantity = value_;
	}

	internal void SetDivisor(decimal value)
	{
		base.UpdateFlags.AddUpdateFlag(8);
		m_divisor = value;
	}

	internal void SetMultiplier(decimal value)
	{
		base.UpdateFlags.AddUpdateFlag(16);
		m_multiplier = value;
	}

	internal void SetSeqNum(int seqNum_)
	{
		m_seqNum = seqNum_;
	}

	internal void SetUnitOfMeasureName(string value)
	{
		base.UpdateFlags.AddUpdateFlag(1);
		m_unitOfMeasureName = value;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.UnreceivedSerialNumber
using Moraware.JobTrackerAPI5;

public class UnreceivedSerialNumber : JTObject
{
	internal enum UnreceivedSerialNumberConditionalFieldUpdateFlags_Enum
	{
		cfufQuantity = 1,
		cfufPostUltimate_PurchaseOrder
	}

	private int m_unreceivedSerialNumberId;

	private int m_purchaseOrderId;

	private int m_purchaseOrderLineId;

	private decimal m_quantity;

	private SerialNumber m_serialNumber;

	public int UnreceivedSerialNumberId => m_unreceivedSerialNumberId;

	public decimal Quantity
	{
		get
		{
			return m_quantity;
		}
		set
		{
			base.UpdateFlags.AddUpdateFlag(1);
			m_quantity = value;
		}
	}

	internal bool ModifiedQuantity => base.UpdateFlags.AreFlagsSet(1);

	public SerialNumber SerialNumber => m_serialNumber;

	internal bool ModifiedSerialNumber
	{
		get
		{
			if (SerialNumber != null)
			{
				if (!SerialNumber.ModifiedBatchNumber && !SerialNumber.ModifiedDescription && !SerialNumber.ModifiedInventoryLocation && !SerialNumber.ModifiedSerialNumberName)
				{
					return SerialNumber.CustomFieldValues.Modified;
				}
				return true;
			}
			return false;
		}
	}

	public int PurchaseOrderId => m_purchaseOrderId;

	public int PurchaseOrderLineId => m_purchaseOrderLineId;

	public UnreceivedSerialNumber(int purchaseOrderLineId_)
	{
		m_purchaseOrderLineId = purchaseOrderLineId_;
	}

	public UnreceivedSerialNumber(int purchaseOrderLineId_, decimal quantity_)
	{
		m_purchaseOrderLineId = purchaseOrderLineId_;
		Quantity = quantity_;
	}

	public UnreceivedSerialNumber(int purchaseOrderLineId_, decimal quantity_, SerialNumber serialNumber_)
	{
		m_purchaseOrderLineId = purchaseOrderLineId_;
		Quantity = quantity_;
		if (serialNumber_ == null)
		{
			serialNumber_ = new SerialNumber(0);
		}
		SetSerialNumber(serialNumber_);
	}

	public UnreceivedSerialNumber(int unreceivedSerialNumberId_, SerialNumber serialNumber_)
		: this(unreceivedSerialNumberId_, 0, 0, 0m, serialNumber_)
	{
	}

	internal UnreceivedSerialNumber(int unreceivedSerialNumberId_, int purchaseOrderId_, int purchaseOrderLineId_, decimal quantity_, SerialNumber serialNumber_)
	{
		m_unreceivedSerialNumberId = unreceivedSerialNumberId_;
		m_purchaseOrderId = purchaseOrderId_;
		m_purchaseOrderLineId = purchaseOrderLineId_;
		m_quantity = quantity_;
		m_serialNumber = serialNumber_;
	}

	internal void SetUnreceivedSerialNumberId(int unreceivedSerialNumberId_)
	{
		m_unreceivedSerialNumberId = unreceivedSerialNumberId_;
	}

	internal void SetSerialNumber(SerialNumber serialNumber_)
	{
		m_serialNumber = serialNumber_;
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.UnsupportedAPIVersionException
using System;
using System.Collections.Generic;
using System.Xml;
using Moraware.JobTrackerAPI5;

public class UnsupportedAPIVersionException : APIException
{
	private List<ServerAPIVersion> m_supportedVersions = new List<ServerAPIVersion>();

	public List<ServerAPIVersion> SupportedVersions
	{
		get
		{
			List<ServerAPIVersion> list = new List<ServerAPIVersion>();
			if (m_supportedVersions != null)
			{
				foreach (ServerAPIVersion supportedVersion in m_supportedVersions)
				{
					list.Add(new ServerAPIVersion(supportedVersion.MinSupportedVersion, supportedVersion.CurrentVersion, supportedVersion.PrereleaseVersion));
				}
			}
			return list;
		}
	}

	internal UnsupportedAPIVersionException(XmlDocument originalDocument_, string message_, XmlElement errorElement_)
		: base(originalDocument_, message_, APIErrorCodes_Enum.UnsupportedVersion)
	{
		try
		{
			List<ServerAPIVersion> list = new List<ServerAPIVersion>();
			int? num = null;
			foreach (XmlElement item in errorElement_.SelectNodes("supportedVersions/version"))
			{
				int num2 = Convert.ToInt32(item.InnerText);
				if (!num.HasValue || num2 < (num ?? 0))
				{
					num = num2;
				}
			}
			foreach (XmlElement item2 in errorElement_.SelectNodes("supportedVersions/version"))
			{
				int currentVersion_ = Convert.ToInt32(item2.InnerText);
				list.Add(new ServerAPIVersion(num ?? 0, currentVersion_, Connection.GetNullableIntFromAttribute(item2, "prereleaseVersion")));
			}
			m_supportedVersions = list;
		}
		catch
		{
		}
	}
}

// JobTrackerAPI5, Version=5.1.0.1, Culture=neutral, PublicKeyToken=null
// Moraware.JobTrackerAPI5.UpdateFlags
using Moraware.JobTrackerAPI5;

internal class UpdateFlags
{
	public enum UpdateFlagsConditionalFieldUpdateFlags_Enum
	{
		cfufNone,
		cfufPostUltimate_HasUpdateFlags
	}

	private int m_updateFlags;

	internal void AddUpdateFlag(int flag_)
	{
		m_updateFlags |= flag_;
	}

	internal void ClearUpdateFlags()
	{
		m_updateFlags = 0;
	}

	internal bool AreFlagsSet(int flagsToTestFor_)
	{
		return Connection.AreAllFlagsSet(flagsToTestFor_, m_updateFlags);
	}

	internal bool AreAnyFlagsSet(int flagstToTestFor_)
	{
		return Connection.AreAnyFlagsSet(flagstToTestFor_, m_updateFlags);
	}
}
