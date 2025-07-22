"mutation login($input: LoginInput!) {
  login(input: $input) {
    user {
      keys {
        identityId
        swid
      }
      identity {
        id
        swid
        email
        username
      }
      oneIDGuest {
        profile {
          swid
          username
          countryCodeDetected
          region
          ageBand
          emailVerified
          firstName
        }
        displayName {
          namespace
          displayName
          proposedDisplayName
          proposedStatus
          moderationStatusDate
        }
        marketing {
          code
          subscribed
          textID
        }
        entitlements {
          digitalAssetName
          digitalAssetSourceName
          productId
          assetId
          effectiveDate
          expirationDate
          policyType
        }
        s2
        etag
        payload
      }
      assignments {
        featureId
        variantId
        version
        type
      }
    }
    oneIDToken {
      access_token
      refresh_token
      swid
      ttl
      refresh_ttl
      scope
      sso
      id_token
      authenticator
      loginValue
      high_trust_expires_in
      initial_grant_in_chain_time
      client_id
      sessionTransferKey
      exp
      iat
      refresh_exp
      high_trust_exp
    }
  }
}",a="mutation register($input: RegisterInput!) {
  register(input: $input) {
    user {
      keys {
        identityId
        swid
      }
      account {
        id
        profiles {
          id
          name
          languagePreferences {
            subtitleAppearance {
              backgroundColor
              size
              description
              edgeStyle
              backgroundOpacity
              windowColor
              textColor
              fontOpacity
              font
              windowOpacity
            }
            subtitleLanguage
            preferSDH
            subtitlesEnabled
            playbackLanguage
            preferAudioDescription
            appLanguage
          }
        }
        defaultProfile
      }
      identity {
        id
        swid
        email
        username
      }
      oneIDGuest {
        profile {
          swid
          referenceId
          testProfileFlag
          username
          prefix
          firstName
          middleName
          lastName
          suffix
          languagePreference
          region
          email
          parentEmail
          dateOfBirth
          gender
          ageBand
          ageBandAssumed
          countryCodeDetected
          emailVerified
          parentEmailVerified
          registrationDate
          dateLastModified
          linkedAccountsAvailable
          status
          addresses {
            addressGuid
            type
            line1
            line2
            line3
            city
            stateProvince
            postalCode
            country
            preferred
            dateCreated
            dateLastModified
          }
          phones {
            phoneGuid
            type
            number
            internationalPrefix
            extension
            preferred
            dateCreated
            dateLastModified
            countryCode
            verified
          }
          pronunciationName
        }
        linkedAccounts {
          swid
          isNRT
          isPrimaryDID
          username
          email
          parentEmail
          dateRegistered
          dateLastLogin
          registeredAffiliate
          loginDomains
          status
        }
        displayName {
          namespace
          displayName
          proposedDisplayName
          proposedStatus
          moderationStatusDate
        }
        geolocation {
          ip
          continentAlpha2
          countryAlpha2
          regionAlpha2
          latitude
          longitude
          usedFallback
        }
        marketing {
          code
          subscribed
          textID
        }
        entitlements {
          digitalAssetName
          digitalAssetSourceName
          productId
          assetId
          effectiveDate
          expirationDate
          policyType
        }
        activities {
          activities {
            activityCode
            activityList {
              dateRequested
              activityPermissionGuid
              approvalStatus
              swid
            }
          }
        }
        s2
        etag
        payload
      }
      assignments {
        featureId
        variantId
        version
        type
      }
    }
    oneIDToken {
      access_token
      refresh_token
      swid
      ttl
      refresh_ttl
      scope
      sso
      id_token
      authenticator
      loginValue
      high_trust_expires_in
      initial_grant_in_chain_time
      client_id
      sessionTransferKey
      exp
      iat
      refresh_exp
      high_trust_exp
    }
  }
}",r="
  query CheckAuthorization($input: CheckAuthorizationInput!) {
    checkAuthorization(input: $input) {
      etag
    }
  }
",o="
  mutation UpdateUserBySwid($input: UpdateUserBySwidInput!) {
    updateUserBySwid(input: $input) {
      user {
        oneIDGuest {
          profile {
            swid
          }
        }
      }
    }
  }
",s="
  mutation UpdateUserBySwid($input: UpdateUserBySwidInput!) {
    updateUserBySwid(input: $input) {
      user {
        oneIDGuest {
          profile {
            swid
            referenceId
            testProfileFlag
            username
            prefix
            firstName
            middleName
            lastName
            suffix
            languagePreference
            region
            email
            parentEmail
            dateOfBirth
            gender
            ageBand
            ageBandAssumed
            countryCodeDetected
            emailVerified
            parentEmailVerified
            registrationDate
            dateLastModified
            linkedAccountsAvailable
            status
            addresses {
              addressGuid
              type
              line1
              line2
              line3
              city
              stateProvince
              postalCode
              country
              preferred
              dateCreated
              dateLastModified
            }
            phones {
              phoneGuid
              type
              number
              internationalPrefix
              extension
              preferred
              dateCreated
              dateLastModified
              countryCode
              verified
            }
            pronunciationName
          }
          linkedAccounts {
            swid
            isNRT
            isPrimaryDID
            username
            email
            parentEmail
            dateRegistered
            dateLastLogin
            registeredAffiliate
            loginDomains
            status
          }
          displayName {
            namespace
            displayName
            proposedDisplayName
            proposedStatus
            moderationStatusDate
          }
          geolocation {
            ip
            continentAlpha2
            countryAlpha2
            regionAlpha2
            latitude
            longitude
            usedFallback
          }
          marketing {
            code
            subscribed
            textID
          }
          entitlements {
            digitalAssetName
            digitalAssetSourceName
            productId
            assetId
            effectiveDate
            expirationDate
            policyType
          }
          activities {
            activities {
              activityCode
              activityList {
                dateRequested
                activityPermissionGuid
                approvalStatus
                swid
              }
            }
          }
          s2
          etag
          payload
        }
      }
    }
  }
",d="mutation updateEmailBySwid($input: UpdateEmailBySwidInput!) {
  updateEmailBySwid(input: $input) {
    accepted
  }
}",u="
mutation redeemOtp($input: RedeemOtpInput!) {
  redeemOtp(input: $input) {
    recoveryToken {
      access_token
      swid
      ttl
      scope
      authenticator
      loginValue
      clickbackType
    }
    accountRecoveryProfiles {
      swid
      isNRT
      isPrimaryDID
      username
      firstName
      lastName
      email
      parentEmail
      dateRegistered
      dateLastLogin
      registeredAffiliate
      registeredDomain
      loginDomains
      status
      isDependant
      ageBand
      isUnresolvableMase
      isOwnedByEmailAssociatedWithUsername
      referenceId
    }
  }
}

",l="
  query RecoveryMethods($input: GetRecoveryMethodsInput!) {
    getRecoveryMethods(input: $input) {
      recoveryMethods {
        mask
        id
        recoveryMethod
      }
    }
  }
",c="mutation loginWithRecoveryToken($input: LoginWithRecoveryTokenInput!) {
  loginWithRecoveryToken(input: $input) {
    user {
      keys {
        identityId
        swid
      }
      account {
        id
        profiles {
          id
          name
          languagePreferences {
            subtitleAppearance {
              backgroundColor
              size
              description
              edgeStyle
              backgroundOpacity
              windowColor
              textColor
              fontOpacity
              font
              windowOpacity
            }
            subtitleLanguage
            preferSDH
            subtitlesEnabled
            playbackLanguage
            preferAudioDescription
            appLanguage
          }
        }
        defaultProfile
      }
      identity {
        id
        swid
        email
        username
      }
      oneIDGuest {
        profile {
          swid
          referenceId
          testProfileFlag
          username
          prefix
          firstName
          middleName
          lastName
          suffix
          languagePreference
          region
          email
          parentEmail
          dateOfBirth
          gender
          ageBand
          ageBandAssumed
          countryCodeDetected
          emailVerified
          parentEmailVerified
          registrationDate
          dateLastModified
          linkedAccountsAvailable
          status
          addresses {
            addressGuid
            type
            line1
            line2
            line3
            city
            stateProvince
            postalCode
            country
            preferred
            dateCreated
            dateLastModified
          }
          phones {
            phoneGuid
            type
            number
            internationalPrefix
            extension
            preferred
            dateCreated
            dateLastModified
            countryCode
            verified
          }
          pronunciationName
        }
        linkedAccounts {
          swid
          isNRT
          isPrimaryDID
          username
          email
          parentEmail
          dateRegistered
          dateLastLogin
          registeredAffiliate
          loginDomains
          status
        }
        displayName {
          namespace
          displayName
          proposedDisplayName
          proposedStatus
          moderationStatusDate
        }
        geolocation {
          ip
          continentAlpha2
          countryAlpha2
          regionAlpha2
          latitude
          longitude
          usedFallback
        }
        marketing {
          code
          subscribed
          textID
        }
        entitlements {
          digitalAssetName
          digitalAssetSourceName
          productId
          assetId
          effectiveDate
          expirationDate
          policyType
        }
        activities {
          activities {
            activityCode
            activityList {
              dateRequested
              activityPermissionGuid
              approvalStatus
              swid
            }
          }
        }
        s2
        etag
        payload
      }
      assignments {
        featureId
        variantId
        version
        type
      }
    }
    oneIDToken {
      access_token
      refresh_token
      swid
      ttl
      refresh_ttl
      scope
      sso
      id_token
      authenticator
      loginValue
      high_trust_expires_in
      initial_grant_in_chain_time
      client_id
      sessionTransferKey
      exp
      iat
      refresh_exp
      high_trust_exp
    }
  }
}",p="
  query checkUserFlow($input: CheckUserFlowInput!) {
    checkUserFlow(input: $input) {
      userFlow
    }
  }
",m="
mutation registerChildForAdult($input: RegisterChildForAdultInput!) {
  registerChildForAdult(input: $input) {
    childProfile {
        profile {
          swid
          referenceId
          testProfileFlag
          username
          prefix
          firstName
          middleName
          lastName
          suffix
          languagePreference
          region
          email
          parentEmail
          dateOfBirth
          gender
          ageBand
          ageBandAssumed
          countryCodeDetected
          emailVerified
          parentEmailVerified
          registrationDate
          dateLastModified
          linkedAccountsAvailable
          status
          addresses {
            addressGuid
            type
            line1
            line2
            line3
            city
            stateProvince
            postalCode
            country
            preferred
            dateCreated
            dateLastModified
          }
          phones {
            phoneGuid
            type
            number
            internationalPrefix
            extension
            preferred
            dateCreated
            dateLastModified
            countryCode
            verified
          }
          pronunciationName
        }
        linkedAccounts {
          swid
          isNRT
          isPrimaryDID
          username
          email
          parentEmail
          dateRegistered
          dateLastLogin
          registeredAffiliate
          loginDomains
          status
        }
        displayName {
          namespace
          displayName
          proposedDisplayName
          proposedStatus
          moderationStatusDate
        }
        geolocation {
          ip
          continentAlpha2
          countryAlpha2
          regionAlpha2
          latitude
          longitude
          usedFallback
        }
        marketing {
          code
          subscribed
          textID
        }
        entitlements {
          digitalAssetName
          digitalAssetSourceName
          productId
          assetId
          effectiveDate
          expirationDate
          policyType
        }
        activities {
          activities {
            activityCode
            activityList {
              dateRequested
              activityPermissionGuid
              approvalStatus
              swid
            }
          }
        }
        s2
        etag
        payload
      }

    }
}
",f="
  mutation RequestEmailOtpForEmailVerification {
    requestEmailOtpForEmailVerification {
      broadcastId
      expirationTime
      sessionId
    }
  }
",g="
  mutation requestSmsOtpForMobileVerification($input: RequestSmsOtpForMobileVerificationInput!) {
    requestSmsOtpForMobileVerification(input: $input) {
      broadcastId
      sessionId
      expirationTime
    }
  }
",y="
  mutation RequestEmailOtpForRecovery($input: RequestEmailOtpForRecoveryInput!) {
    requestEmailOtpForRecovery(input: $input) {
      broadcastId
      sessionId
      expirationTime
    }
  }
",I="
  mutation requestSmsOtpForRecovery($input: RequestSmsOtpForRecoveryInput!) {
    requestSmsOtpForRecovery(input: $input) {
      broadcastId
      sessionId
      expirationTime
    }
  }
",_="
  mutation RequestEmailOtpForUpdateCredential {
    requestEmailOtpForUpdateCredential {
      broadcastId
      sessionId
      expirationTime
    }
  }
",v="
  mutation requestSmsOtpForUpdateCredential($input: RequestSmsOtpForUpdateCredentialInput!) {
    requestSmsOtpForUpdateCredential(input: $input) {
      broadcastId
      sessionId
      expirationTime
    }
  }
",A="
  mutation updatePasswordBySwid($input: UpdatePasswordBySwidInput!) {
    updatePasswordBySwid(input: $input) {
      user {
        oneIDGuest {
          etag
        }
      }
      oneIDToken {
        access_token
        refresh_token
        swid
        ttl
        refresh_ttl
        scope
        sso
        id_token
        authenticator
        loginValue
        high_trust_expires_in
        initial_grant_in_chain_time
        client_id
        sessionTransferKey
      }
    }
  }
",h="
  mutation updateMarketingAssertions($input: UpdateMarketingAssertionsInput!) {
    updateMarketingAssertions(input: $input) {
      broadcastIds
    }
  }
",E="
mutation deleteUserBySwid($input: DeleteUserBySwidInput!) {
  deleteUserBySwid(input: $input) {
    accepted
  }
}",N="
  query getUserBySwid($input: GetUserBySwidInput!) {
  getUserBySwid(input: $input) {
    user {
      keys {
        identityId
        swid
      }
      account {
        id
        profiles {
          id
          name
          languagePreferences {
            subtitleAppearance {
              backgroundColor
              size
              description
              edgeStyle
              backgroundOpacity
              windowColor
              textColor
              fontOpacity
              font
              windowOpacity
            }
            subtitleLanguage
            preferSDH
            subtitlesEnabled
            playbackLanguage
            preferAudioDescription
            appLanguage
          }
        }
        defaultProfile
      }
      identity {
        id
        swid
        email
        username
      }
      oneIDGuest {
        profile {
          swid
          referenceId
          testProfileFlag
          username
          prefix
          firstName
          middleName
          lastName
          suffix
          languagePreference
          region
          email
          parentEmail
          dateOfBirth
          gender
          ageBand
          ageBandAssumed
          countryCodeDetected
          emailVerified
          parentEmailVerified
          registrationDate
          dateLastModified
          linkedAccountsAvailable
          status
          addresses {
            addressGuid
            type
            line1
            line2
            line3
            city
            stateProvince
            postalCode
            country
            preferred
            dateCreated
            dateLastModified
          }
          phones {
            phoneGuid
            type
            number
            internationalPrefix
            extension
            preferred
            dateCreated
            dateLastModified
            countryCode
            verified
          }
          pronunciationName
        }
        linkedAccounts {
          swid
          isNRT
          isPrimaryDID
          username
          email
          parentEmail
          dateRegistered
          dateLastLogin
          registeredAffiliate
          loginDomains
          status
        }
        displayName {
          namespace
          displayName
          proposedDisplayName
          proposedStatus
          moderationStatusDate
        }
        geolocation {
          ip
          continentAlpha2
          countryAlpha2
          regionAlpha2
          latitude
          longitude
          usedFallback
        }
        marketing {
          code
          subscribed
          textID
        }
        entitlements {
          digitalAssetName
          digitalAssetSourceName
          productId
          assetId
          effectiveDate
          expirationDate
          policyType
        }
        activities {
          activities {
            activityCode
            activityList {
              dateRequested
              activityPermissionGuid
              approvalStatus
              swid
            }
          }
        }
        s2
        etag
        payload
      }
      assignments {
        featureId
        variantId
        version
        type
      }
    }
  }
}